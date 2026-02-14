import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import os from 'node:os';
import path from 'node:path';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js';
import { createGalleyServer } from '../../src/server.js';
import { createStorage } from '../../src/core/storage.js';
import { createConfigLoader } from '../../src/core/config.js';
import { createLogger } from '../../src/core/logger.js';
import type { Storage } from '../../src/core/storage.js';

function createTestDeps(tmpDir: string) {
  const storage = createStorage({ baseDir: tmpDir });

  const pkgRoot = path.resolve(import.meta.dirname, '../../');
  const configLoader = createConfigLoader({
    defaultConfigDir: path.join(pkgRoot, 'config'),
    promptsDir: path.join(pkgRoot, 'prompts'),
  });

  const logger = createLogger({ level: 'warning' });

  return { storage, configLoader, logger };
}

async function setupClientServer(tmpDir: string) {
  const deps = createTestDeps(tmpDir);
  await deps.storage.initDataDir();

  const server = createGalleyServer(deps);
  const client = new Client({ name: 'test-client', version: '1.0.0' });

  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();

  await Promise.all([
    client.connect(clientTransport),
    server.connect(serverTransport),
  ]);

  return { client, server, storage: deps.storage };
}

function getToolText(result: unknown): string {
  const r = result as { content?: Array<{ text?: string }> };
  const text = r.content?.[0]?.text;
  if (typeof text === 'string') return text;
  throw new Error('No text content in tool result');
}

function parseToolJson(result: unknown): unknown {
  return JSON.parse(getToolText(result));
}

describe('MCP Server Integration', () => {
  let tmpDir: string;
  let client: Client;
  let storage: Storage;
  let mcpServer: ReturnType<typeof createGalleyServer>;

  beforeEach(async () => {
    tmpDir = path.join(os.tmpdir(), `galley-integration-${crypto.randomUUID().slice(0, 8)}`);
    const result = await setupClientServer(tmpDir);
    client = result.client;
    storage = result.storage;
    mcpServer = result.server;
  });

  afterEach(async () => {
    await client.close();
    await mcpServer.close();
    await fs.rm(tmpDir, { recursive: true, force: true });
  });

  // =============================================
  // Tools Discovery
  // =============================================
  describe('Tools Discovery', () => {
    it('should list all 12 registered tools', async () => {
      const { tools } = await client.listTools();
      const toolNames = tools.map((t) => t.name).sort();

      expect(toolNames).toEqual([
        'complete_hearing',
        'create_session',
        'delete_session',
        'export_all',
        'export_iac',
        'export_mermaid',
        'export_summary',
        'get_hearing_result',
        'list_sessions',
        'save_answer',
        'save_answers_batch',
        'save_architecture',
      ]);
    });

    it('should have descriptions and input schemas for all tools', async () => {
      const { tools } = await client.listTools();
      for (const tool of tools) {
        expect(tool.description).toBeTruthy();
        expect(tool.inputSchema).toBeDefined();
      }
    });
  });

  // =============================================
  // Resources Discovery
  // =============================================
  describe('Resources Discovery', () => {
    it('should list static resources', async () => {
      const { resources } = await client.listResources();
      const uris = resources.map((r) => r.uri).sort();

      expect(uris).toContain('galley://templates/hearing-questions');
      expect(uris).toContain('galley://templates/hearing-flow');
      expect(uris).toContain('galley://schemas/hearing-result');
      expect(uris).toContain('galley://sessions');
      expect(uris).toContain('galley://references/oci-services');
      expect(uris).toContain('galley://references/oci-architectures');
      expect(uris).toContain('galley://references/oci-terraform');
    });

    it('should list resource templates', async () => {
      const { resourceTemplates } = await client.listResourceTemplates();
      const templates = resourceTemplates.map((t) => t.uriTemplate);

      expect(templates).toContain('galley://sessions/{session_id}');
    });

    it('should read hearing-questions resource', async () => {
      const { contents } = await client.readResource({ uri: 'galley://templates/hearing-questions' });
      expect(contents).toHaveLength(1);
      const text = (contents[0] as { text: string }).text;
      const data = JSON.parse(text) as Record<string, unknown>;
      expect(data).toHaveProperty('categories');
    });

    it('should read hearing-flow resource', async () => {
      const { contents } = await client.readResource({ uri: 'galley://templates/hearing-flow' });
      expect(contents).toHaveLength(1);
      const text = (contents[0] as { text: string }).text;
      const data = JSON.parse(text) as Record<string, unknown>;
      expect(data).toHaveProperty('default_order');
    });

    it('should read oci-services resource', async () => {
      const { contents } = await client.readResource({ uri: 'galley://references/oci-services' });
      expect(contents).toHaveLength(1);
      const text = (contents[0] as { text: string }).text;
      const data = JSON.parse(text) as { services: unknown[] };
      expect(data).toHaveProperty('services');
      expect(data.services.length).toBeGreaterThan(0);
    });

    it('should read oci-architectures resource', async () => {
      const { contents } = await client.readResource({ uri: 'galley://references/oci-architectures' });
      expect(contents).toHaveLength(1);
      const text = (contents[0] as { text: string }).text;
      const data = JSON.parse(text) as Record<string, unknown>;
      expect(data).toHaveProperty('patterns');
    });

    it('should read oci-terraform resource', async () => {
      const { contents } = await client.readResource({ uri: 'galley://references/oci-terraform' });
      expect(contents).toHaveLength(1);
      const text = (contents[0] as { text: string }).text;
      const data = JSON.parse(text) as Record<string, unknown>;
      expect(data).toHaveProperty('resources');
    });
  });

  // =============================================
  // Prompts Discovery
  // =============================================
  describe('Prompts Discovery', () => {
    it('should list all 3 registered prompts', async () => {
      const { prompts } = await client.listPrompts();
      const promptNames = prompts.map((p) => p.name).sort();

      expect(promptNames).toEqual([
        'generate-architecture',
        'resume-hearing',
        'start-hearing',
      ]);
    });

    it('should get start-hearing prompt', async () => {
      const result = await client.getPrompt({
        name: 'start-hearing',
        arguments: { project_description: '在庫管理システム' },
      });

      expect(result.messages).toHaveLength(1);
      expect(result.messages[0]?.role).toBe('user');
      const content = result.messages[0]?.content;
      if (typeof content === 'object' && 'text' in content) {
        expect(content.text).toContain('在庫管理システム');
      }
    });

    it('should get resume-hearing prompt', async () => {
      const fakeId = crypto.randomUUID();
      const result = await client.getPrompt({
        name: 'resume-hearing',
        arguments: { session_id: fakeId },
      });

      expect(result.messages).toHaveLength(1);
      const content = result.messages[0]?.content;
      if (typeof content === 'object' && 'text' in content) {
        expect(content.text).toContain(fakeId);
      }
    });

    it('should get generate-architecture prompt', async () => {
      const fakeId = crypto.randomUUID();
      const result = await client.getPrompt({
        name: 'generate-architecture',
        arguments: { session_id: fakeId },
      });

      expect(result.messages).toHaveLength(1);
      const content = result.messages[0]?.content;
      if (typeof content === 'object' && 'text' in content) {
        expect(content.text).toContain(fakeId);
      }
    });
  });

  // =============================================
  // Hearing Flow E2E
  // =============================================
  describe('Hearing Flow E2E', () => {
    it('should create session, save answers, complete hearing, and get result', async () => {
      // Step 1: Create session
      const createResult = await client.callTool({
        name: 'create_session',
        arguments: { project_description: '在庫管理システム' },
      });
      const created = parseToolJson(createResult) as { session_id: string };
      expect(created.session_id).toBeTruthy();

      const sessionId = created.session_id;

      // Step 2: Save single answer
      const saveResult = await client.callTool({
        name: 'save_answer',
        arguments: {
          session_id: sessionId,
          category: 'scale',
          question_id: 'concurrent_users',
          value: '500',
          source: 'user_selected',
        },
      });
      const saved = parseToolJson(saveResult) as { saved: boolean };
      expect(saved.saved).toBe(true);

      // Step 3: Save answers batch
      const batchResult = await client.callTool({
        name: 'save_answers_batch',
        arguments: {
          session_id: sessionId,
          answers: [
            {
              category: 'availability',
              question_id: 'sla_target',
              value: '99.9%',
              source: 'user_selected',
            },
            {
              category: 'availability',
              question_id: 'dr_requirement',
              value: '同一リージョン内HA',
              source: 'estimated',
              estimation: {
                confidence_label: 'general_estimate',
                reasoning: '製造業では通常同一リージョン内HAで十分',
              },
            },
            {
              category: 'project_overview',
              question_id: 'industry',
              value: '製造業',
              source: 'user_selected',
            },
          ],
        },
      });
      const batched = parseToolJson(batchResult) as { saved: boolean; count: number };
      expect(batched.saved).toBe(true);
      expect(batched.count).toBe(3);

      // Step 4: Get hearing result before completion
      const preResult = await client.callTool({
        name: 'get_hearing_result',
        arguments: { session_id: sessionId },
      });
      const preHearing = parseToolJson(preResult) as {
        metadata: { status: string };
        requirements: { scale: { concurrent_users: { value: string } } };
      };
      expect(preHearing.metadata.status).toBe('in_progress');
      expect(preHearing.requirements.scale.concurrent_users.value).toBe('500');

      // Step 5: Complete hearing
      const completeResult = await client.callTool({
        name: 'complete_hearing',
        arguments: { session_id: sessionId },
      });
      const completed = parseToolJson(completeResult) as {
        status: string;
        summary: { total_categories: number; answered_categories: number };
      };
      expect(completed.status).toBe('completed');
      expect(completed.summary.answered_categories).toBeGreaterThan(0);

      // Step 6: Verify hearing result is now completed
      const postResult = await client.callTool({
        name: 'get_hearing_result',
        arguments: { session_id: sessionId },
      });
      const postHearing = parseToolJson(postResult) as { metadata: { status: string } };
      expect(postHearing.metadata.status).toBe('completed');
    });

    it('should reject saving to completed session', async () => {
      // Create and complete a session
      const createResult = await client.callTool({
        name: 'create_session',
        arguments: { project_description: 'test' },
      });
      const created = parseToolJson(createResult) as { session_id: string };
      const sessionId = created.session_id;

      await client.callTool({
        name: 'complete_hearing',
        arguments: { session_id: sessionId },
      });

      // Try to save an answer after completion
      const result = await client.callTool({
        name: 'save_answer',
        arguments: {
          session_id: sessionId,
          category: 'scale',
          question_id: 'concurrent_users',
          value: '500',
          source: 'user_selected',
        },
      });

      const text = getToolText(result);
      expect(text).toContain('Error');
      expect(text).toContain('INVALID_SESSION_STATUS');
    });
  });

  // =============================================
  // Session Management
  // =============================================
  describe('Session Management', () => {
    it('should list sessions with filtering', async () => {
      // Create two sessions
      const r1 = await client.callTool({
        name: 'create_session',
        arguments: { project_description: 'Project A' },
      });
      const s1 = parseToolJson(r1) as { session_id: string };

      const r2 = await client.callTool({
        name: 'create_session',
        arguments: { project_description: 'Project B' },
      });
      const s2 = parseToolJson(r2) as { session_id: string };

      // Complete one session
      await client.callTool({
        name: 'complete_hearing',
        arguments: { session_id: s1.session_id },
      });

      // List all sessions
      const allResult = await client.callTool({
        name: 'list_sessions',
        arguments: {},
      });
      const allSessions = parseToolJson(allResult) as Array<{ session_id: string }>;
      expect(allSessions).toHaveLength(2);

      // List only in_progress sessions
      const inProgressResult = await client.callTool({
        name: 'list_sessions',
        arguments: { status: 'in_progress' },
      });
      const inProgressSessions = parseToolJson(inProgressResult) as Array<{ session_id: string }>;
      expect(inProgressSessions).toHaveLength(1);
      expect(inProgressSessions[0]?.session_id).toBe(s2.session_id);

      // List only completed sessions
      const completedResult = await client.callTool({
        name: 'list_sessions',
        arguments: { status: 'completed' },
      });
      const completedSessions = parseToolJson(completedResult) as Array<{ session_id: string }>;
      expect(completedSessions).toHaveLength(1);
      expect(completedSessions[0]?.session_id).toBe(s1.session_id);
    });

    it('should delete session and its output', async () => {
      const createResult = await client.callTool({
        name: 'create_session',
        arguments: { project_description: 'To be deleted' },
      });
      const created = parseToolJson(createResult) as { session_id: string };
      const sessionId = created.session_id;

      // Create some output
      await storage.writeText(`output/${sessionId}/summary.md`, '# Test');

      // Delete session
      const deleteResult = await client.callTool({
        name: 'delete_session',
        arguments: { session_id: sessionId },
      });
      const deleted = parseToolJson(deleteResult) as { deleted: boolean };
      expect(deleted.deleted).toBe(true);

      // Verify files are removed
      expect(await storage.exists(`sessions/${sessionId}/session.json`)).toBe(false);
      expect(await storage.exists(`output/${sessionId}/summary.md`)).toBe(false);
    });

    it('should return error for non-existent session', async () => {
      const fakeId = crypto.randomUUID();
      const result = await client.callTool({
        name: 'delete_session',
        arguments: { session_id: fakeId },
      });

      const text = getToolText(result);
      expect(text).toContain('Error');
      expect(text).toContain('SESSION_NOT_FOUND');
    });

    it('should read session detail via resource template', async () => {
      const createResult = await client.callTool({
        name: 'create_session',
        arguments: { project_description: 'Resource template test' },
      });
      const created = parseToolJson(createResult) as { session_id: string };

      const { contents } = await client.readResource({
        uri: `galley://sessions/${created.session_id}`,
      });
      expect(contents).toHaveLength(1);
      const text = (contents[0] as { text: string }).text;
      const data = JSON.parse(text) as Record<string, unknown>;
      expect(data.session).toHaveProperty('session_id', created.session_id);
      expect(data.hearing_result).toHaveProperty('metadata');
    });

    it('should list sessions via sessions resource', async () => {
      await client.callTool({
        name: 'create_session',
        arguments: { project_description: 'Session list test' },
      });

      const { contents } = await client.readResource({
        uri: 'galley://sessions',
      });
      expect(contents).toHaveLength(1);
      const text = (contents[0] as { text: string }).text;
      const sessions = JSON.parse(text) as unknown[];
      expect(sessions.length).toBeGreaterThanOrEqual(1);
    });
  });

  // =============================================
  // Architecture & Export E2E
  // =============================================
  describe('Architecture & Export E2E', () => {
    let sessionId: string;

    beforeEach(async () => {
      // Create and populate a session
      const createResult = await client.callTool({
        name: 'create_session',
        arguments: { project_description: '在庫管理システム' },
      });
      const created = parseToolJson(createResult) as { session_id: string };
      sessionId = created.session_id;

      await client.callTool({
        name: 'save_answers_batch',
        arguments: {
          session_id: sessionId,
          answers: [
            { category: 'scale', question_id: 'concurrent_users', value: '500', source: 'user_selected' },
            { category: 'project_overview', question_id: 'industry', value: '製造業', source: 'user_selected' },
          ],
        },
      });

      await client.callTool({
        name: 'complete_hearing',
        arguments: { session_id: sessionId },
      });
    });

    it('should save architecture and export summary', async () => {
      // Save architecture
      const archResult = await client.callTool({
        name: 'save_architecture',
        arguments: {
          session_id: sessionId,
          components: [
            { category: 'コンピュート', service_name: 'OKE', purpose: 'アプリケーション実行基盤', reason: 'コンテナ化による柔軟なスケーリング' },
            { category: 'データベース', service_name: 'Autonomous Database', purpose: 'データ永続化', reason: '運用負荷の低減' },
          ],
          decisions: [
            { category: 'compute', decision: 'OKEを採用', reason: 'マイクロサービス対応' },
          ],
          warnings: [
            { type: 'backup', message: 'バックアップ未設定', severity: 'warning' },
          ],
        },
      });
      const archSaved = parseToolJson(archResult) as { saved: boolean; component_count: number };
      expect(archSaved.saved).toBe(true);
      expect(archSaved.component_count).toBe(2);

      // Export summary (includes architecture)
      const summaryResult = await client.callTool({
        name: 'export_summary',
        arguments: { session_id: sessionId },
      });
      const summaryOutput = parseToolJson(summaryResult) as { file_path: string };
      expect(summaryOutput.file_path).toContain('summary.md');

      // Verify summary content
      const summaryContent = await storage.readText(summaryOutput.file_path);
      expect(summaryContent).toContain('# 要件サマリー');
      expect(summaryContent).toContain('在庫管理システム');
      expect(summaryContent).toContain('OKE');
      expect(summaryContent).toContain('バックアップ未設定');
    });

    it('should export mermaid diagram', async () => {
      const mermaidCode = 'graph TD\n  A[LB] --> B[OKE]\n  B --> C[ADB]';
      const result = await client.callTool({
        name: 'export_mermaid',
        arguments: {
          session_id: sessionId,
          mermaid_code: mermaidCode,
        },
      });
      const output = parseToolJson(result) as { file_path: string };
      expect(output.file_path).toContain('architecture.mmd');

      const content = await storage.readText(output.file_path);
      expect(content).toContain('graph TD');
    });

    it('should export IaC files with validation', async () => {
      const result = await client.callTool({
        name: 'export_iac',
        arguments: {
          session_id: sessionId,
          files: [
            { name: 'main.tf', content: 'resource "oci_core_vcn" "main" {}' },
            { name: 'variables.tf', content: 'variable "compartment_ocid" {}' },
          ],
        },
      });
      const output = parseToolJson(result) as { file_paths: string[] };
      expect(output.file_paths).toHaveLength(2);

      const mainTf = await storage.readText(output.file_paths[0] ?? '');
      expect(mainTf).toContain('oci_core_vcn');
    });

    it('should reject IaC files with invalid filenames', async () => {
      const result = await client.callTool({
        name: 'export_iac',
        arguments: {
          session_id: sessionId,
          files: [
            { name: '../../../evil.tf', content: 'evil content' },
          ],
        },
      });

      const text = getToolText(result);
      expect(text).toContain('Error');
      expect(text).toContain('INVALID_FILENAME');
    });

    it('should export all artifacts at once', async () => {
      // Save architecture first
      await client.callTool({
        name: 'save_architecture',
        arguments: {
          session_id: sessionId,
          components: [
            { category: 'コンピュート', service_name: 'OKE', purpose: '実行基盤', reason: 'スケーラビリティ' },
          ],
          decisions: [{ category: 'compute', decision: 'OKEを採用', reason: '柔軟性' }],
          warnings: [],
        },
      });

      const result = await client.callTool({
        name: 'export_all',
        arguments: {
          session_id: sessionId,
          mermaid_code: 'graph TD\n  A --> B',
          iac_files: [
            { name: 'main.tf', content: 'resource "oci_core_vcn" "main" {}' },
          ],
        },
      });
      const output = parseToolJson(result) as { output_dir: string; files: string[] };
      expect(output.files.length).toBeGreaterThanOrEqual(3);
      expect(output.files.some((f: string) => f.endsWith('summary.md'))).toBe(true);
      expect(output.files.some((f: string) => f.endsWith('architecture.mmd'))).toBe(true);
      expect(output.files.some((f: string) => f.endsWith('main.tf'))).toBe(true);
    });

    it('should export all without optional artifacts', async () => {
      const result = await client.callTool({
        name: 'export_all',
        arguments: { session_id: sessionId },
      });
      const output = parseToolJson(result) as { output_dir: string; files: string[] };
      expect(output.files).toHaveLength(1);
      expect(output.files[0]).toContain('summary.md');
    });
  });

  // =============================================
  // Error Handling
  // =============================================
  describe('Error Handling', () => {
    it('should return structured error for non-existent session on get_hearing_result', async () => {
      const result = await client.callTool({
        name: 'get_hearing_result',
        arguments: { session_id: crypto.randomUUID() },
      });

      const text = getToolText(result);
      expect(text).toContain('Error');
    });

    it('should return structured error for save_architecture on non-existent session', async () => {
      const result = await client.callTool({
        name: 'save_architecture',
        arguments: {
          session_id: crypto.randomUUID(),
          components: [],
          decisions: [],
          warnings: [],
        },
      });

      const text = getToolText(result);
      expect(text).toContain('Error');
      expect(text).toContain('SESSION_NOT_FOUND');
    });

    it('should return error when completing already completed session', async () => {
      const createResult = await client.callTool({
        name: 'create_session',
        arguments: { project_description: 'test' },
      });
      const created = parseToolJson(createResult) as { session_id: string };

      await client.callTool({
        name: 'complete_hearing',
        arguments: { session_id: created.session_id },
      });

      const result = await client.callTool({
        name: 'complete_hearing',
        arguments: { session_id: created.session_id },
      });

      const text = getToolText(result);
      expect(text).toContain('Error');
      expect(text).toContain('INVALID_SESSION_STATUS');
    });
  });
});
