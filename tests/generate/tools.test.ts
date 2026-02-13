import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import os from 'node:os';
import path from 'node:path';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import { createStorage } from '../../src/core/storage.js';
import type { Storage } from '../../src/core/storage.js';
import { GalleyError } from '../../src/core/errors.js';
import { buildSummaryMarkdown } from '../../src/generate/tools.js';
import type { HearingResult } from '../../src/types/hearing.js';
import type { ArchitectureOutput } from '../../src/types/architecture.js';

function makeHearingResult(): HearingResult {
  return {
    metadata: {
      hearing_id: crypto.randomUUID(),
      created_at: new Date().toISOString(),
      version: '1.0.0',
      status: 'completed',
    },
    project_overview: {
      description: '在庫管理システム',
      industry: { value: '製造業', source: 'user_selected' },
    },
    requirements: {
      scale: {
        concurrent_users: { value: '500', source: 'user_selected' },
      },
      availability: {
        sla_target: { value: '99.9%', source: 'user_selected' },
        dr_requirement: {
          value: '同一リージョン内HA',
          source: 'estimated',
          estimation: {
            confidence_label: 'general_estimate',
            reasoning: '製造業では通常同一リージョン内HAで十分',
          },
        },
      },
    },
  };
}

function makeArchitecture(sessionId: string): ArchitectureOutput {
  return {
    session_id: sessionId,
    components: [
      {
        category: 'コンピュート',
        service_name: 'OKE',
        purpose: 'アプリケーション実行基盤',
        reason: 'コンテナ化による柔軟なスケーリング',
      },
    ],
    decisions: [
      { category: 'compute', decision: 'OKEを採用', reason: 'マイクロサービス対応' },
    ],
    warnings: [
      { type: 'backup', message: 'バックアップ未設定', severity: 'warning' },
    ],
  };
}

describe('buildSummaryMarkdown', () => {
  it('should generate summary with confirmed and estimated items', () => {
    const hr = makeHearingResult();
    const md = buildSummaryMarkdown(hr);

    expect(md).toContain('# 要件サマリー');
    expect(md).toContain('在庫管理システム');
    expect(md).toContain('✅ **concurrent_users**: 500');
    expect(md).toContain('🔶 **dr_requirement**: 同一リージョン内HA');
    expect(md).toContain('_(推測:');
  });

  it('should include architecture section when provided', () => {
    const hr = makeHearingResult();
    const arch = makeArchitecture(crypto.randomUUID());
    const md = buildSummaryMarkdown(hr, arch);

    expect(md).toContain('## アーキテクチャ');
    expect(md).toContain('OKE');
    expect(md).toContain('### 警告');
    expect(md).toContain('バックアップ未設定');
  });

  it('should not include architecture section when not provided', () => {
    const hr = makeHearingResult();
    const md = buildSummaryMarkdown(hr);

    expect(md).not.toContain('## アーキテクチャ');
  });
});

describe('Generate Tools Integration', () => {
  let tmpDir: string;
  let storage: Storage;

  beforeEach(async () => {
    tmpDir = path.join(os.tmpdir(), `galley-gen-test-${crypto.randomUUID().slice(0, 8)}`);
    storage = createStorage({ baseDir: tmpDir });
    await storage.initDataDir();
  });

  afterEach(async () => {
    await fs.rm(tmpDir, { recursive: true, force: true });
  });

  it('should save architecture to session directory', async () => {
    const sessionId = crypto.randomUUID();
    await storage.writeJson(`sessions/${sessionId}/session.json`, {
      session_id: sessionId,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      status: 'completed',
      project_description: 'test',
    });

    const arch = makeArchitecture(sessionId);
    await storage.writeJson(`sessions/${sessionId}/architecture.json`, arch);

    const saved = await storage.readJson<ArchitectureOutput>(`sessions/${sessionId}/architecture.json`);
    expect(saved.components).toHaveLength(1);
    expect(saved.components[0]?.service_name).toBe('OKE');
  });

  it('should write summary markdown to output directory', async () => {
    const sessionId = crypto.randomUUID();
    const hr = makeHearingResult();

    await storage.writeJson(`sessions/${sessionId}/hearing-result.json`, hr);

    const markdown = buildSummaryMarkdown(hr);
    await storage.writeText(`output/${sessionId}/summary.md`, markdown);

    const content = await storage.readText(`output/${sessionId}/summary.md`);
    expect(content).toContain('# 要件サマリー');
  });

  it('should write mermaid file to output directory', async () => {
    const sessionId = crypto.randomUUID();
    const mermaidCode = 'graph TD\n  A[LB] --> B[OKE]\n  B --> C[ADB]';

    await storage.writeText(`output/${sessionId}/architecture.mmd`, mermaidCode);

    const content = await storage.readText(`output/${sessionId}/architecture.mmd`);
    expect(content).toContain('graph TD');
  });

  it('should write terraform files with filename validation', async () => {
    const sessionId = crypto.randomUUID();

    storage.validateFilename('main.tf');
    await storage.writeText(`output/${sessionId}/terraform/main.tf`, 'resource "oci_core_vcn" {}');

    const content = await storage.readText(`output/${sessionId}/terraform/main.tf`);
    expect(content).toContain('oci_core_vcn');
  });

  it('should reject invalid terraform filenames', () => {
    expect(() => storage.validateFilename('../../../evil.tf')).toThrow(GalleyError);
    expect(() => storage.validateFilename('path/to/file.tf')).toThrow(GalleyError);
  });

  it('should export all artifacts', async () => {
    const sessionId = crypto.randomUUID();
    const hr = makeHearingResult();

    await storage.writeJson(`sessions/${sessionId}/hearing-result.json`, hr);

    // Export summary
    const markdown = buildSummaryMarkdown(hr);
    await storage.writeText(`output/${sessionId}/summary.md`, markdown);

    // Export mermaid
    await storage.writeText(`output/${sessionId}/architecture.mmd`, 'graph TD\n  A --> B');

    // Export IaC
    storage.validateFilename('main.tf');
    await storage.writeText(`output/${sessionId}/terraform/main.tf`, 'resource {}');

    expect(await storage.exists(`output/${sessionId}/summary.md`)).toBe(true);
    expect(await storage.exists(`output/${sessionId}/architecture.mmd`)).toBe(true);
    expect(await storage.exists(`output/${sessionId}/terraform/main.tf`)).toBe(true);
  });
});
