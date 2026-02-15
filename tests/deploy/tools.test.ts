import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import os from 'node:os';
import path from 'node:path';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js';
import { createStorage } from '../../src/core/storage.js';
import { createLogger } from '../../src/core/logger.js';
import { registerDeployTools } from '../../src/deploy/tools.js';
import type { Storage } from '../../src/core/storage.js';
import type { Logger } from '../../src/core/logger.js';
import type { OciCli, OciCliResult } from '../../src/core/oci-cli.js';

function createMockOciCli(overrides?: Partial<OciCli>): OciCli {
  return {
    checkVersion: vi.fn<() => Promise<string>>().mockResolvedValue('3.41.0'),
    checkZip: vi.fn<() => Promise<string>>().mockResolvedValue('Zip 3.0'),
    execute: vi.fn<() => Promise<OciCliResult>>().mockResolvedValue({ stdout: '{}', parsed: {} }),
    createZip: vi.fn<() => Promise<void>>().mockResolvedValue(undefined),
    ...overrides,
  };
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

describe('Deploy Tools', () => {
  let tmpDir: string;
  let storage: Storage;
  let logger: Logger;
  let mockOciCli: OciCli;
  let client: Client;
  let server: McpServer;

  beforeEach(async () => {
    tmpDir = path.join(os.tmpdir(), `galley-deploy-test-${crypto.randomUUID().slice(0, 8)}`);
    storage = createStorage({ baseDir: tmpDir });
    await storage.initDataDir();
    logger = createLogger({ level: 'warning' });
    mockOciCli = createMockOciCli();

    server = new McpServer(
      { name: 'galley-test', version: '0.1.0' },
      { capabilities: { tools: {} } },
    );
    registerDeployTools(server, storage, logger, mockOciCli);

    client = new Client({ name: 'test-client', version: '1.0.0' });
    const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
    await Promise.all([
      client.connect(clientTransport),
      server.connect(serverTransport),
    ]);
  });

  afterEach(async () => {
    await client.close();
    await server.close();
    await fs.rm(tmpDir, { recursive: true, force: true });
  });

  describe('check_oci_cli', () => {
    it('should return versions when both tools are available', async () => {
      const result = await client.callTool({ name: 'check_oci_cli', arguments: {} });
      const data = parseToolJson(result) as { oci_cli: string; zip: string; errors: string[] };

      expect(data.oci_cli).toBe('3.41.0');
      expect(data.zip).toBe('Zip 3.0');
      expect(data.errors).toHaveLength(0);
    });

    it('should report errors when tools are missing', async () => {
      const { GalleyError } = await import('../../src/core/errors.js');
      mockOciCli = createMockOciCli({
        checkVersion: vi.fn().mockRejectedValue(new GalleyError('OCI_CLI_NOT_FOUND', 'oci not found')),
        checkZip: vi.fn().mockRejectedValue(new GalleyError('OCI_CLI_NOT_FOUND', 'zip not found')),
      });

      // Re-register with new mock
      server = new McpServer(
        { name: 'galley-test', version: '0.1.0' },
        { capabilities: { tools: {} } },
      );
      registerDeployTools(server, storage, logger, mockOciCli);

      const newClient = new Client({ name: 'test-client', version: '1.0.0' });
      const [ct, st] = InMemoryTransport.createLinkedPair();
      await Promise.all([newClient.connect(ct), server.connect(st)]);

      const result = await newClient.callTool({ name: 'check_oci_cli', arguments: {} });
      const data = parseToolJson(result) as { errors: string[] };

      expect(data.errors).toHaveLength(2);
      expect(data.errors[0]).toContain('oci');
      expect(data.errors[1]).toContain('zip');

      await newClient.close();
    });
  });

  describe('create_rm_stack', () => {
    let sessionId: string;

    beforeEach(async () => {
      sessionId = crypto.randomUUID();
      // Create session
      await storage.writeJson(`sessions/${sessionId}/session.json`, {
        session_id: sessionId,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        status: 'completed',
        project_description: 'test',
      });
      // Create terraform output
      await storage.writeText(`output/${sessionId}/terraform/main.tf`, 'resource {}');
    });

    it('should create stack and save deploy state', async () => {
      const stackId = 'ocid1.ormstack.oc1.ap-tokyo-1.aaa';
      (mockOciCli.execute as ReturnType<typeof vi.fn>).mockResolvedValue({
        stdout: JSON.stringify({ data: { id: stackId } }),
        parsed: { data: { id: stackId } },
      });

      const result = await client.callTool({
        name: 'create_rm_stack',
        arguments: {
          session_id: sessionId,
          compartment_id: 'ocid1.compartment.oc1..aaa',
          display_name: 'test-stack',
        },
      });

      const data = parseToolJson(result) as { stack_id: string; display_name: string };
      expect(data.stack_id).toBe(stackId);
      expect(data.display_name).toBe('test-stack');

      // Verify zip was created
      expect(mockOciCli.createZip).toHaveBeenCalledOnce();

      // Verify deploy state was saved
      const state = await storage.readJson<{ stack_id: string; jobs: unknown[] }>(
        `sessions/${sessionId}/deploy-state.json`,
      );
      expect(state.stack_id).toBe(stackId);
      expect(state.jobs).toHaveLength(0);
    });

    it('should return error for missing session', async () => {
      const result = await client.callTool({
        name: 'create_rm_stack',
        arguments: {
          session_id: crypto.randomUUID(),
          compartment_id: 'ocid1.compartment.oc1..aaa',
        },
      });

      const text = getToolText(result);
      expect(text).toContain('SESSION_NOT_FOUND');
    });

    it('should return error when terraform files not exported', async () => {
      const noTfSession = crypto.randomUUID();
      await storage.writeJson(`sessions/${noTfSession}/session.json`, {
        session_id: noTfSession,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        status: 'completed',
        project_description: 'test',
      });

      const result = await client.callTool({
        name: 'create_rm_stack',
        arguments: {
          session_id: noTfSession,
          compartment_id: 'ocid1.compartment.oc1..aaa',
        },
      });

      const text = getToolText(result);
      expect(text).toContain('TERRAFORM_NOT_EXPORTED');
    });
  });

  describe('run_rm_plan', () => {
    let sessionId: string;

    beforeEach(async () => {
      sessionId = crypto.randomUUID();
      // Create deploy state with stack
      await storage.writeJson(`sessions/${sessionId}/deploy-state.json`, {
        session_id: sessionId,
        stack_id: 'ocid1.ormstack.oc1..aaa',
        jobs: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
    });

    it('should create plan job and update deploy state', async () => {
      const jobId = 'ocid1.ormjob.oc1..plan';
      (mockOciCli.execute as ReturnType<typeof vi.fn>).mockResolvedValue({
        stdout: JSON.stringify({ data: { id: jobId, 'lifecycle-state': 'ACCEPTED' } }),
        parsed: { data: { id: jobId, 'lifecycle-state': 'ACCEPTED' } },
      });

      const result = await client.callTool({
        name: 'run_rm_plan',
        arguments: { session_id: sessionId },
      });

      const data = parseToolJson(result) as { job_id: string; status: string };
      expect(data.job_id).toBe(jobId);
      expect(data.status).toBe('ACCEPTED');

      // Verify deploy state was updated
      const state = await storage.readJson<{ jobs: Array<{ job_id: string; job_type: string }> }>(
        `sessions/${sessionId}/deploy-state.json`,
      );
      expect(state.jobs).toHaveLength(1);
      expect(state.jobs[0]?.job_type).toBe('plan');
    });

    it('should return error when no deploy state exists', async () => {
      const result = await client.callTool({
        name: 'run_rm_plan',
        arguments: { session_id: crypto.randomUUID() },
      });

      const text = getToolText(result);
      expect(text).toContain('DEPLOY_ERROR');
    });
  });

  describe('run_rm_apply', () => {
    let sessionId: string;

    beforeEach(async () => {
      sessionId = crypto.randomUUID();
      await storage.writeJson(`sessions/${sessionId}/deploy-state.json`, {
        session_id: sessionId,
        stack_id: 'ocid1.ormstack.oc1..aaa',
        jobs: [
          {
            job_id: 'ocid1.ormjob.oc1..plan',
            job_type: 'plan',
            status: 'SUCCEEDED',
            created_at: new Date().toISOString(),
          },
        ],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
    });

    it('should create apply job with AUTO_APPROVED', async () => {
      const jobId = 'ocid1.ormjob.oc1..apply';
      (mockOciCli.execute as ReturnType<typeof vi.fn>).mockResolvedValue({
        stdout: JSON.stringify({ data: { id: jobId, 'lifecycle-state': 'ACCEPTED' } }),
        parsed: { data: { id: jobId, 'lifecycle-state': 'ACCEPTED' } },
      });

      const result = await client.callTool({
        name: 'run_rm_apply',
        arguments: {
          session_id: sessionId,
          execution_plan_strategy: 'AUTO_APPROVED',
        },
      });

      const data = parseToolJson(result) as { job_id: string; status: string };
      expect(data.job_id).toBe(jobId);

      // Verify execution args
      const executeCall = (mockOciCli.execute as ReturnType<typeof vi.fn>).mock.calls[0] as [string[], Record<string, string>];
      expect(executeCall[1]).toHaveProperty('execution-plan-strategy', 'AUTO_APPROVED');
    });

    it('should create apply job with FROM_PLAN_JOB_ID using latest plan', async () => {
      const jobId = 'ocid1.ormjob.oc1..apply2';
      (mockOciCli.execute as ReturnType<typeof vi.fn>).mockResolvedValue({
        stdout: JSON.stringify({ data: { id: jobId, 'lifecycle-state': 'ACCEPTED' } }),
        parsed: { data: { id: jobId, 'lifecycle-state': 'ACCEPTED' } },
      });

      const result = await client.callTool({
        name: 'run_rm_apply',
        arguments: {
          session_id: sessionId,
          execution_plan_strategy: 'FROM_PLAN_JOB_ID',
        },
      });

      const data = parseToolJson(result) as { job_id: string };
      expect(data.job_id).toBe(jobId);

      // Verify it picked up the plan job from state
      const executeCall = (mockOciCli.execute as ReturnType<typeof vi.fn>).mock.calls[0] as [string[], Record<string, string>];
      expect(executeCall[1]).toHaveProperty('execution-plan-job-id', 'ocid1.ormjob.oc1..plan');
    });

    it('should error when FROM_PLAN_JOB_ID but no plan exists', async () => {
      const noPlanSession = crypto.randomUUID();
      await storage.writeJson(`sessions/${noPlanSession}/deploy-state.json`, {
        session_id: noPlanSession,
        stack_id: 'ocid1.ormstack.oc1..aaa',
        jobs: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });

      const result = await client.callTool({
        name: 'run_rm_apply',
        arguments: {
          session_id: noPlanSession,
          execution_plan_strategy: 'FROM_PLAN_JOB_ID',
        },
      });

      const text = getToolText(result);
      expect(text).toContain('DEPLOY_ERROR');
      expect(text).toContain('plan_job_id');
    });
  });

  describe('get_rm_job_status', () => {
    let sessionId: string;

    beforeEach(async () => {
      sessionId = crypto.randomUUID();
      await storage.writeJson(`sessions/${sessionId}/deploy-state.json`, {
        session_id: sessionId,
        stack_id: 'ocid1.ormstack.oc1..aaa',
        jobs: [
          {
            job_id: 'ocid1.ormjob.oc1..job1',
            job_type: 'plan',
            status: 'IN_PROGRESS',
            created_at: new Date().toISOString(),
          },
        ],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
    });

    it('should return job status', async () => {
      (mockOciCli.execute as ReturnType<typeof vi.fn>).mockResolvedValue({
        stdout: JSON.stringify({ data: { id: 'ocid1.ormjob.oc1..job1', 'lifecycle-state': 'SUCCEEDED', operation: 'PLAN' } }),
        parsed: { data: { id: 'ocid1.ormjob.oc1..job1', 'lifecycle-state': 'SUCCEEDED', operation: 'PLAN' } },
      });

      const result = await client.callTool({
        name: 'get_rm_job_status',
        arguments: {
          session_id: sessionId,
          job_id: 'ocid1.ormjob.oc1..job1',
        },
      });

      const data = parseToolJson(result) as { job_id: string; status: string; operation: string };
      expect(data.status).toBe('SUCCEEDED');
      expect(data.operation).toBe('PLAN');

      // Verify deploy state was updated
      const state = await storage.readJson<{ jobs: Array<{ status: string }> }>(
        `sessions/${sessionId}/deploy-state.json`,
      );
      expect(state.jobs[0]?.status).toBe('SUCCEEDED');
    });

    it('should include logs when requested', async () => {
      const executeMock = mockOciCli.execute as ReturnType<typeof vi.fn>;
      executeMock
        .mockResolvedValueOnce({
          stdout: JSON.stringify({ data: { id: 'ocid1.ormjob.oc1..job1', 'lifecycle-state': 'SUCCEEDED' } }),
          parsed: { data: { id: 'ocid1.ormjob.oc1..job1', 'lifecycle-state': 'SUCCEEDED' } },
        })
        .mockResolvedValueOnce({
          stdout: JSON.stringify({ data: [{ message: 'Terraform init...' }, { message: 'Plan: 3 to add' }] }),
          parsed: { data: [{ message: 'Terraform init...' }, { message: 'Plan: 3 to add' }] },
        });

      const result = await client.callTool({
        name: 'get_rm_job_status',
        arguments: {
          session_id: sessionId,
          job_id: 'ocid1.ormjob.oc1..job1',
          include_logs: true,
        },
      });

      const data = parseToolJson(result) as { logs: string };
      expect(data.logs).toContain('Terraform init...');
      expect(data.logs).toContain('Plan: 3 to add');
    });
  });
});
