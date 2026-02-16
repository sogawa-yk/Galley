import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import os from 'node:os';
import path from 'node:path';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import { createLogger } from '../../src/core/logger.js';
import { createStorage } from '../../src/core/storage.js';

interface LogEntry {
  timestamp: string;
  level: string;
  tool: string;
  message: string;
  data?: unknown;
}

function parseLogEntry(line: string): LogEntry {
  return JSON.parse(line) as LogEntry;
}

describe('Logger', () => {
  describe('forSession', () => {
    let tmpDir: string;

    beforeEach(async () => {
      tmpDir = path.join(os.tmpdir(), `galley-logger-test-${crypto.randomUUID().slice(0, 8)}`);
      await fs.mkdir(tmpDir, { recursive: true });
    });

    afterEach(async () => {
      await fs.rm(tmpDir, { recursive: true, force: true });
    });

    it('should write JSON Lines to session log file', async () => {
      const logger = createLogger({ level: 'info' });
      const storage = createStorage({ baseDir: tmpDir });
      const slog = logger.forSession('sess-1', storage, 'create_session');

      slog.info('Session created', { id: 'sess-1' });

      // Wait for async appendText to complete
      await vi.waitFor(async () => {
        const content = await fs.readFile(path.join(tmpDir, 'sessions/sess-1/galley.log'), 'utf-8');
        expect(content.trim().length).toBeGreaterThan(0);
      });

      const content = await fs.readFile(path.join(tmpDir, 'sessions/sess-1/galley.log'), 'utf-8');
      const entry = parseLogEntry(content.trim());
      expect(entry.level).toBe('info');
      expect(entry.tool).toBe('create_session');
      expect(entry.message).toBe('Session created');
      expect(entry.data).toEqual({ id: 'sess-1' });
      expect(entry.timestamp).toBeDefined();
    });

    it('should append multiple entries', async () => {
      const logger = createLogger({ level: 'info' });
      const storage = createStorage({ baseDir: tmpDir });
      const slog = logger.forSession('sess-2', storage, 'test_tool');

      slog.info('First');
      slog.warning('Second');

      await vi.waitFor(async () => {
        const content = await fs.readFile(path.join(tmpDir, 'sessions/sess-2/galley.log'), 'utf-8');
        const lines = content.trim().split('\n');
        expect(lines.length).toBe(2);
      });

      const content = await fs.readFile(path.join(tmpDir, 'sessions/sess-2/galley.log'), 'utf-8');
      const lines = content.trim().split('\n');
      expect(parseLogEntry(lines[0] ?? '').message).toBe('First');
      expect(parseLogEntry(lines[1] ?? '').message).toBe('Second');
    });

    it('should respect log level filter', async () => {
      const logger = createLogger({ level: 'warning' });
      const storage = createStorage({ baseDir: tmpDir });
      const slog = logger.forSession('sess-3', storage, 'test_tool');

      slog.debug('should not appear');
      slog.info('should not appear');
      slog.warning('should appear');

      await vi.waitFor(async () => {
        const content = await fs.readFile(path.join(tmpDir, 'sessions/sess-3/galley.log'), 'utf-8');
        expect(content.trim().length).toBeGreaterThan(0);
      });

      const content = await fs.readFile(path.join(tmpDir, 'sessions/sess-3/galley.log'), 'utf-8');
      const lines = content.trim().split('\n');
      expect(lines).toHaveLength(1);
      expect(parseLogEntry(lines[0] ?? '').level).toBe('warning');
    });

    it('should delegate to parent logger for stderr/MCP output', () => {
      const logger = createLogger({ level: 'info' });
      const storage = createStorage({ baseDir: tmpDir });
      const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const slog = logger.forSession('sess-4', storage, 'test_tool');
      slog.info('test message');

      expect(errorSpy).toHaveBeenCalledWith(expect.stringContaining('test message'));
      errorSpy.mockRestore();
    });

    it('should not throw when file write fails', () => {
      const logger = createLogger({ level: 'info' });
      const storage = createStorage({ baseDir: tmpDir });

      // Mock appendText to reject
      vi.spyOn(storage, 'appendText').mockRejectedValue(new Error('disk full'));

      const slog = logger.forSession('sess-5', storage, 'test_tool');

      // This should not throw
      expect(() => slog.info('test')).not.toThrow();
    });

    it('should omit data field when no data provided', async () => {
      const logger = createLogger({ level: 'info' });
      const storage = createStorage({ baseDir: tmpDir });
      const slog = logger.forSession('sess-6', storage, 'test_tool');

      slog.info('no data message');

      await vi.waitFor(async () => {
        const content = await fs.readFile(path.join(tmpDir, 'sessions/sess-6/galley.log'), 'utf-8');
        expect(content.trim().length).toBeGreaterThan(0);
      });

      const content = await fs.readFile(path.join(tmpDir, 'sessions/sess-6/galley.log'), 'utf-8');
      const entry = parseLogEntry(content.trim());
      expect(entry).not.toHaveProperty('data');
    });
  });
});
