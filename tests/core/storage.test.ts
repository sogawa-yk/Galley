import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import os from 'node:os';
import path from 'node:path';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import { createStorage } from '../../src/core/storage.js';
import { GalleyError } from '../../src/core/errors.js';

describe('Storage', () => {
  let tmpDir: string;

  beforeEach(async () => {
    tmpDir = path.join(os.tmpdir(), `galley-test-${crypto.randomUUID().slice(0, 8)}`);
    await fs.mkdir(tmpDir, { recursive: true });
  });

  afterEach(async () => {
    await fs.rm(tmpDir, { recursive: true, force: true });
  });

  describe('initDataDir', () => {
    it('should create sessions and output directories', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      await storage.initDataDir();

      const sessionsExists = await fs
        .access(path.join(tmpDir, 'sessions'))
        .then(() => true)
        .catch(() => false);
      const outputExists = await fs
        .access(path.join(tmpDir, 'output'))
        .then(() => true)
        .catch(() => false);

      expect(sessionsExists).toBe(true);
      expect(outputExists).toBe(true);
    });
  });

  describe('validatePath', () => {
    it('should resolve valid relative paths', () => {
      const storage = createStorage({ baseDir: tmpDir });
      const resolved = storage.validatePath('sessions/abc/session.json');
      expect(resolved).toBe(path.join(tmpDir, 'sessions/abc/session.json'));
    });

    it('should throw PATH_TRAVERSAL for directory traversal', () => {
      const storage = createStorage({ baseDir: tmpDir });
      expect(() => storage.validatePath('../../etc/passwd')).toThrow(GalleyError);
      expect(() => storage.validatePath('../../etc/passwd')).toThrow(/Path traversal detected/);
    });

    it('should throw PATH_TRAVERSAL for absolute paths outside base', () => {
      const storage = createStorage({ baseDir: tmpDir });
      expect(() => storage.validatePath('/etc/passwd')).toThrow(GalleyError);
    });
  });

  describe('validateFilename', () => {
    it('should accept valid filenames', () => {
      const storage = createStorage({ baseDir: tmpDir });
      expect(() => storage.validateFilename('main.tf')).not.toThrow();
      expect(() => storage.validateFilename('provider.tf')).not.toThrow();
    });

    it('should reject filenames with ..', () => {
      const storage = createStorage({ baseDir: tmpDir });
      expect(() => storage.validateFilename('..secret')).toThrow(GalleyError);
      expect(() => storage.validateFilename('..secret')).toThrow(/Invalid filename/);
    });

    it('should reject filenames with slashes', () => {
      const storage = createStorage({ baseDir: tmpDir });
      expect(() => storage.validateFilename('a/b.tf')).toThrow(GalleyError);
      expect(() => storage.validateFilename('a\\b.tf')).toThrow(GalleyError);
    });
  });

  describe('writeJson / readJson', () => {
    it('should write and read JSON data', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      const data = { name: 'test', value: 42 };

      await storage.writeJson('test.json', data);
      const result = await storage.readJson<typeof data>('test.json');

      expect(result).toEqual(data);
    });

    it('should create parent directories', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      await storage.writeJson('a/b/c.json', { ok: true });
      const result = await storage.readJson<{ ok: boolean }>('a/b/c.json');
      expect(result).toEqual({ ok: true });
    });

    it('should perform atomic writes (no partial files on failure)', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      await storage.writeJson('atomic.json', { first: true });

      // Verify the file exists and has correct content
      const content = await fs.readFile(path.join(tmpDir, 'atomic.json'), 'utf-8');
      expect(JSON.parse(content)).toEqual({ first: true });

      // Verify no tmp files remain
      const files = await fs.readdir(tmpDir);
      expect(files.filter((f) => f.includes('.tmp.'))).toHaveLength(0);
    });

    it('should throw FILE_READ_ERROR for non-existent file', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      await expect(storage.readJson('nonexistent.json')).rejects.toThrow(GalleyError);
      try {
        await storage.readJson('nonexistent.json');
      } catch (error) {
        expect((error as GalleyError).code).toBe('FILE_READ_ERROR');
      }
    });

    it('should throw FILE_READ_ERROR for invalid JSON', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      await fs.writeFile(path.join(tmpDir, 'bad.json'), '{invalid', 'utf-8');
      await expect(storage.readJson('bad.json')).rejects.toThrow(GalleyError);
      try {
        await storage.readJson('bad.json');
      } catch (error) {
        expect((error as GalleyError).code).toBe('FILE_READ_ERROR');
        expect((error as GalleyError).message).toMatch(/Invalid JSON/);
      }
    });
  });

  describe('writeText / readText', () => {
    it('should write and read text content', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      await storage.writeText('test.md', '# Hello\n\nWorld');
      const result = await storage.readText('test.md');
      expect(result).toBe('# Hello\n\nWorld');
    });

    it('should throw FILE_READ_ERROR for non-existent file', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      await expect(storage.readText('missing.txt')).rejects.toThrow(GalleyError);
    });
  });

  describe('appendText', () => {
    it('should create file and append content', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      await storage.appendText('log.txt', 'line1\n');
      const result = await fs.readFile(path.join(tmpDir, 'log.txt'), 'utf-8');
      expect(result).toBe('line1\n');
    });

    it('should append to existing file', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      await storage.appendText('log.txt', 'line1\n');
      await storage.appendText('log.txt', 'line2\n');
      const result = await fs.readFile(path.join(tmpDir, 'log.txt'), 'utf-8');
      expect(result).toBe('line1\nline2\n');
    });

    it('should create parent directories', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      await storage.appendText('a/b/log.txt', 'data\n');
      const result = await fs.readFile(path.join(tmpDir, 'a/b/log.txt'), 'utf-8');
      expect(result).toBe('data\n');
    });

    it('should reject path traversal', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      await expect(storage.appendText('../../etc/passwd', 'x')).rejects.toThrow(GalleyError);
      await expect(storage.appendText('../../etc/passwd', 'x')).rejects.toThrow(/Path traversal detected/);
    });
  });

  describe('exists', () => {
    it('should return true for existing file', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      await storage.writeJson('exists.json', {});
      expect(await storage.exists('exists.json')).toBe(true);
    });

    it('should return false for non-existent file', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      expect(await storage.exists('nope.json')).toBe(false);
    });
  });

  describe('listDirs', () => {
    it('should list directories', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      await fs.mkdir(path.join(tmpDir, 'sessions', 'aaa'), { recursive: true });
      await fs.mkdir(path.join(tmpDir, 'sessions', 'bbb'), { recursive: true });
      await fs.writeFile(path.join(tmpDir, 'sessions', 'file.txt'), 'x');

      const dirs = await storage.listDirs('sessions');
      expect(dirs.sort()).toEqual(['aaa', 'bbb']);
    });

    it('should return empty array for non-existent directory', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      const dirs = await storage.listDirs('nonexistent');
      expect(dirs).toEqual([]);
    });
  });

  describe('removeDir', () => {
    it('should remove directory recursively', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      await storage.writeJson('sessions/abc/session.json', { id: 'abc' });
      await storage.removeDir('sessions/abc');
      expect(await storage.exists('sessions/abc')).toBe(false);
    });

    it('should not throw for non-existent directory', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      await expect(storage.removeDir('nonexistent')).resolves.not.toThrow();
    });
  });

  describe('ensureDir', () => {
    it('should create nested directories', async () => {
      const storage = createStorage({ baseDir: tmpDir });
      await storage.ensureDir('a/b/c');
      const stat = await fs.stat(path.join(tmpDir, 'a/b/c'));
      expect(stat.isDirectory()).toBe(true);
    });
  });
});
