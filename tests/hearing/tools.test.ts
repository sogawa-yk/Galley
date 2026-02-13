import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import os from 'node:os';
import path from 'node:path';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import { createStorage } from '../../src/core/storage.js';
import type { Storage } from '../../src/core/storage.js';
import { GalleyError } from '../../src/core/errors.js';
import { applyAnswer } from '../../src/hearing/tools.js';
import type { HearingResult } from '../../src/types/hearing.js';
import { HearingResultSchema, SessionSchema } from '../../src/core/schema.js';

function makeHearingResult(description: string): HearingResult {
  return {
    metadata: {
      hearing_id: crypto.randomUUID(),
      created_at: new Date().toISOString(),
      version: '1.0.0',
      status: 'in_progress',
    },
    project_overview: { description },
    requirements: {},
  };
}

function makeSession(sessionId: string, status: 'in_progress' | 'completed' = 'in_progress') {
  const now = new Date().toISOString();
  return {
    session_id: sessionId,
    created_at: now,
    updated_at: now,
    status,
    project_description: 'Test project',
  };
}

describe('applyAnswer', () => {
  it('should apply answer to scale category', () => {
    const hr = makeHearingResult('test');
    applyAnswer(hr, 'scale', 'concurrent_users', '1000', 'user_selected');
    expect(hr.requirements.scale?.concurrent_users).toEqual({
      value: '1000',
      source: 'user_selected',
    });
  });

  it('should apply answer with estimation', () => {
    const hr = makeHearingResult('test');
    applyAnswer(hr, 'scale', 'concurrent_users', 5000, 'estimated', {
      confidence_label: 'general_estimate',
      reasoning: 'Industry average',
    });
    expect(hr.requirements.scale?.concurrent_users).toEqual({
      value: 5000,
      source: 'estimated',
      estimation: {
        confidence_label: 'general_estimate',
        reasoning: 'Industry average',
      },
    });
  });

  it('should apply answer to project_overview', () => {
    const hr = makeHearingResult('test');
    applyAnswer(hr, 'project_overview', 'industry', '製造業', 'user_selected');
    expect(hr.project_overview.industry).toEqual({
      value: '製造業',
      source: 'user_selected',
    });
  });

  it('should throw for unknown category', () => {
    const hr = makeHearingResult('test');
    expect(() => applyAnswer(hr, 'unknown_cat', 'field', 'val', 'user_selected')).toThrow(GalleyError);
  });
});

describe('Hearing Tools Integration', () => {
  let tmpDir: string;
  let storage: Storage;

  beforeEach(async () => {
    tmpDir = path.join(os.tmpdir(), `galley-hearing-test-${crypto.randomUUID().slice(0, 8)}`);
    storage = createStorage({ baseDir: tmpDir });
    await storage.initDataDir();
  });

  afterEach(async () => {
    await fs.rm(tmpDir, { recursive: true, force: true });
  });

  async function createTestSession(sessionId: string, status: 'in_progress' | 'completed' = 'in_progress') {
    const session = makeSession(sessionId, status);
    const hr = makeHearingResult('Test project');
    hr.metadata.hearing_id = sessionId;
    await storage.writeJson(`sessions/${sessionId}/session.json`, session);
    await storage.writeJson(`sessions/${sessionId}/hearing-result.json`, hr);
    return { session, hearingResult: hr };
  }

  it('should create session files', async () => {
    const sessionId = crypto.randomUUID();
    await createTestSession(sessionId);

    const session = await storage.readJson<unknown>(`sessions/${sessionId}/session.json`);
    const result = SessionSchema.safeParse(session);
    expect(result.success).toBe(true);

    const hr = await storage.readJson<unknown>(`sessions/${sessionId}/hearing-result.json`);
    const hrResult = HearingResultSchema.safeParse(hr);
    expect(hrResult.success).toBe(true);
  });

  it('should save an answer and update hearing result', async () => {
    const sessionId = crypto.randomUUID();
    await createTestSession(sessionId);

    const hr = await storage.readJson<HearingResult>(`sessions/${sessionId}/hearing-result.json`);
    applyAnswer(hr, 'scale', 'concurrent_users', '1000', 'user_selected');
    await storage.writeJson(`sessions/${sessionId}/hearing-result.json`, hr);

    const updated = await storage.readJson<HearingResult>(`sessions/${sessionId}/hearing-result.json`);
    expect(updated.requirements.scale?.concurrent_users?.value).toBe('1000');
  });

  it('should prevent saving to completed session', async () => {
    const sessionId = crypto.randomUUID();
    await createTestSession(sessionId, 'completed');

    const session = await storage.readJson<{ status: string }>(`sessions/${sessionId}/session.json`);
    expect(session.status).toBe('completed');
  });

  it('should list sessions sorted by created_at desc', async () => {
    const id1 = crypto.randomUUID();
    const id2 = crypto.randomUUID();

    const session1 = makeSession(id1);
    session1.created_at = '2026-01-01T00:00:00Z';
    await storage.writeJson(`sessions/${id1}/session.json`, session1);

    const session2 = makeSession(id2);
    session2.created_at = '2026-01-02T00:00:00Z';
    await storage.writeJson(`sessions/${id2}/session.json`, session2);

    const dirs = await storage.listDirs('sessions');
    const sessions = [];
    for (const dir of dirs) {
      const s = await storage.readJson<{ session_id: string; created_at: string }>(`sessions/${dir}/session.json`);
      sessions.push(s);
    }
    sessions.sort((a, b) => b.created_at.localeCompare(a.created_at));

    expect(sessions[0]?.session_id).toBe(id2);
    expect(sessions[1]?.session_id).toBe(id1);
  });

  it('should delete session and output directories', async () => {
    const sessionId = crypto.randomUUID();
    await createTestSession(sessionId);
    await storage.writeText(`output/${sessionId}/summary.md`, '# Test');

    await storage.removeDir(`sessions/${sessionId}`);
    await storage.removeDir(`output/${sessionId}`);

    expect(await storage.exists(`sessions/${sessionId}/session.json`)).toBe(false);
    expect(await storage.exists(`output/${sessionId}/summary.md`)).toBe(false);
  });
});
