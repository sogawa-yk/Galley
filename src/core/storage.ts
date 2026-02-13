import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { GalleyError } from './errors.js';

export interface StorageOptions {
  baseDir: string;
}

export interface Storage {
  ensureDir(relativePath: string): Promise<void>;
  initDataDir(): Promise<void>;
  readJson<T>(relativePath: string): Promise<T>;
  writeJson(relativePath: string, data: unknown): Promise<void>;
  exists(relativePath: string): Promise<boolean>;
  readText(relativePath: string): Promise<string>;
  writeText(relativePath: string, content: string): Promise<void>;
  listDirs(relativePath: string): Promise<string[]>;
  removeDir(relativePath: string): Promise<void>;
  validatePath(relativePath: string): string;
  validateFilename(filename: string): void;
}

export function createStorage(options: StorageOptions): Storage {
  const baseDir = path.resolve(options.baseDir);

  function validatePath(relativePath: string): string {
    const resolved = path.resolve(baseDir, relativePath);
    if (!resolved.startsWith(baseDir + path.sep) && resolved !== baseDir) {
      throw new GalleyError('PATH_TRAVERSAL', `Path traversal detected: ${relativePath}`);
    }
    return resolved;
  }

  function validateFilename(filename: string): void {
    if (filename.includes('..') || filename.includes('/') || filename.includes('\\')) {
      throw new GalleyError('INVALID_FILENAME', `Invalid filename: ${filename}`);
    }
  }

  function wrapFsError(error: unknown, operation: 'read' | 'write', relativePath: string): never {
    if (error instanceof GalleyError) throw error;
    const nodeError = error as NodeJS.ErrnoException;
    if (nodeError.code === 'ENOENT') {
      throw new GalleyError('FILE_READ_ERROR', `File not found: ${relativePath}`, error);
    }
    if (nodeError.code === 'EACCES') {
      throw new GalleyError(
        operation === 'read' ? 'FILE_READ_ERROR' : 'FILE_WRITE_ERROR',
        `Permission denied: ${relativePath}`,
        error,
      );
    }
    throw new GalleyError(
      operation === 'read' ? 'FILE_READ_ERROR' : 'FILE_WRITE_ERROR',
      `${operation === 'read' ? 'Read' : 'Write'} failed: ${relativePath}`,
      error,
    );
  }

  async function atomicWrite(absolutePath: string, content: string): Promise<void> {
    const dir = path.dirname(absolutePath);
    await fs.mkdir(dir, { recursive: true });
    const tmpPath = `${absolutePath}.tmp.${crypto.randomUUID().slice(0, 8)}`;
    try {
      await fs.writeFile(tmpPath, content, 'utf-8');
      await fs.rename(tmpPath, absolutePath);
    } catch (error) {
      await fs.unlink(tmpPath).catch(() => {});
      throw error;
    }
  }

  return {
    validatePath,
    validateFilename,

    async ensureDir(relativePath: string): Promise<void> {
      const absolutePath = validatePath(relativePath);
      try {
        await fs.mkdir(absolutePath, { recursive: true });
      } catch (error) {
        wrapFsError(error, 'write', relativePath);
      }
    },

    async initDataDir(): Promise<void> {
      await fs.mkdir(path.join(baseDir, 'sessions'), { recursive: true, mode: 0o700 });
      await fs.mkdir(path.join(baseDir, 'output'), { recursive: true, mode: 0o700 });
    },

    async readJson<T>(relativePath: string): Promise<T> {
      const absolutePath = validatePath(relativePath);
      try {
        const content = await fs.readFile(absolutePath, 'utf-8');
        return JSON.parse(content) as T;
      } catch (error) {
        if (error instanceof SyntaxError) {
          throw new GalleyError('FILE_READ_ERROR', `Invalid JSON: ${relativePath}`, error);
        }
        return wrapFsError(error, 'read', relativePath);
      }
    },

    async writeJson(relativePath: string, data: unknown): Promise<void> {
      const absolutePath = validatePath(relativePath);
      try {
        await atomicWrite(absolutePath, JSON.stringify(data, null, 2) + '\n');
      } catch (error) {
        wrapFsError(error, 'write', relativePath);
      }
    },

    async exists(relativePath: string): Promise<boolean> {
      const absolutePath = validatePath(relativePath);
      try {
        await fs.access(absolutePath);
        return true;
      } catch {
        return false;
      }
    },

    async readText(relativePath: string): Promise<string> {
      const absolutePath = validatePath(relativePath);
      try {
        return await fs.readFile(absolutePath, 'utf-8');
      } catch (error) {
        return wrapFsError(error, 'read', relativePath);
      }
    },

    async writeText(relativePath: string, content: string): Promise<void> {
      const absolutePath = validatePath(relativePath);
      try {
        await atomicWrite(absolutePath, content);
      } catch (error) {
        wrapFsError(error, 'write', relativePath);
      }
    },

    async listDirs(relativePath: string): Promise<string[]> {
      const absolutePath = validatePath(relativePath);
      try {
        const entries = await fs.readdir(absolutePath, { withFileTypes: true });
        return entries.filter((e) => e.isDirectory()).map((e) => e.name);
      } catch (error) {
        const nodeError = error as NodeJS.ErrnoException;
        if (nodeError.code === 'ENOENT') return [];
        return wrapFsError(error, 'read', relativePath);
      }
    },

    async removeDir(relativePath: string): Promise<void> {
      const absolutePath = validatePath(relativePath);
      try {
        await fs.rm(absolutePath, { recursive: true, force: true });
      } catch (error) {
        wrapFsError(error, 'write', relativePath);
      }
    },
  };
}
