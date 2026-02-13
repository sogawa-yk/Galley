import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import os from 'node:os';
import path from 'node:path';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import { z } from 'zod';
import { createConfigLoader, renderTemplate } from '../../src/core/config.js';
import { GalleyError } from '../../src/core/errors.js';

describe('ConfigLoader', () => {
  let tmpDir: string;
  let defaultConfigDir: string;
  let userConfigDir: string;
  let overrideConfigDir: string;
  let promptsDir: string;

  beforeEach(async () => {
    tmpDir = path.join(os.tmpdir(), `galley-config-test-${crypto.randomUUID().slice(0, 8)}`);
    defaultConfigDir = path.join(tmpDir, 'default');
    userConfigDir = path.join(tmpDir, 'user');
    overrideConfigDir = path.join(tmpDir, 'override');
    promptsDir = path.join(tmpDir, 'prompts');

    await fs.mkdir(defaultConfigDir, { recursive: true });
    await fs.mkdir(userConfigDir, { recursive: true });
    await fs.mkdir(overrideConfigDir, { recursive: true });
    await fs.mkdir(promptsDir, { recursive: true });
  });

  afterEach(async () => {
    await fs.rm(tmpDir, { recursive: true, force: true });
  });

  const TestSchema = z.object({
    version: z.string(),
    name: z.string(),
  });

  describe('loadConfig', () => {
    it('should load from default config dir', async () => {
      await fs.writeFile(
        path.join(defaultConfigDir, 'test.yaml'),
        'version: "1.0"\nname: default',
      );
      const loader = createConfigLoader({
        defaultConfigDir,
        promptsDir,
      });
      const result = await loader.loadConfig('test.yaml', TestSchema);
      expect(result).toEqual({ version: '1.0', name: 'default' });
    });

    it('should prefer user config over default', async () => {
      await fs.writeFile(
        path.join(defaultConfigDir, 'test.yaml'),
        'version: "1.0"\nname: default',
      );
      await fs.writeFile(
        path.join(userConfigDir, 'test.yaml'),
        'version: "1.0"\nname: user',
      );
      const loader = createConfigLoader({
        defaultConfigDir,
        userConfigDir,
        promptsDir,
      });
      const result = await loader.loadConfig('test.yaml', TestSchema);
      expect(result).toEqual({ version: '1.0', name: 'user' });
    });

    it('should prefer override config over user and default', async () => {
      await fs.writeFile(
        path.join(defaultConfigDir, 'test.yaml'),
        'version: "1.0"\nname: default',
      );
      await fs.writeFile(
        path.join(userConfigDir, 'test.yaml'),
        'version: "1.0"\nname: user',
      );
      await fs.writeFile(
        path.join(overrideConfigDir, 'test.yaml'),
        'version: "1.0"\nname: override',
      );
      const loader = createConfigLoader({
        defaultConfigDir,
        userConfigDir,
        overrideConfigDir,
        promptsDir,
      });
      const result = await loader.loadConfig('test.yaml', TestSchema);
      expect(result).toEqual({ version: '1.0', name: 'override' });
    });

    it('should throw CONFIG_LOAD_ERROR for missing file', async () => {
      const loader = createConfigLoader({
        defaultConfigDir,
        promptsDir,
      });
      await expect(loader.loadConfig('missing.yaml', TestSchema)).rejects.toThrow(GalleyError);
      try {
        await loader.loadConfig('missing.yaml', TestSchema);
      } catch (error) {
        expect((error as GalleyError).code).toBe('CONFIG_LOAD_ERROR');
      }
    });

    it('should throw CONFIG_LOAD_ERROR for invalid YAML schema', async () => {
      await fs.writeFile(
        path.join(defaultConfigDir, 'bad.yaml'),
        'version: "1.0"\nextra_field: true',
      );
      const loader = createConfigLoader({
        defaultConfigDir,
        promptsDir,
      });
      await expect(loader.loadConfig('bad.yaml', TestSchema)).rejects.toThrow(GalleyError);
      try {
        await loader.loadConfig('bad.yaml', TestSchema);
      } catch (error) {
        expect((error as GalleyError).code).toBe('CONFIG_LOAD_ERROR');
        expect((error as GalleyError).message).toMatch(/Validation failed/);
      }
    });
  });

  describe('loadPromptTemplate', () => {
    it('should load prompt template file', async () => {
      await fs.writeFile(
        path.join(promptsDir, 'test.md'),
        '# Hello {{name}}',
      );
      const loader = createConfigLoader({
        defaultConfigDir,
        promptsDir,
      });
      const template = await loader.loadPromptTemplate('test.md');
      expect(template).toBe('# Hello {{name}}');
    });

    it('should throw CONFIG_LOAD_ERROR for missing template', async () => {
      const loader = createConfigLoader({
        defaultConfigDir,
        promptsDir,
      });
      await expect(loader.loadPromptTemplate('missing.md')).rejects.toThrow(GalleyError);
    });
  });

  describe('getResolvedConfigDir', () => {
    it('should return override dir when set', () => {
      const loader = createConfigLoader({
        defaultConfigDir,
        userConfigDir,
        overrideConfigDir,
        promptsDir,
      });
      expect(loader.getResolvedConfigDir()).toBe(overrideConfigDir);
    });

    it('should return user dir when override is not set', () => {
      const loader = createConfigLoader({
        defaultConfigDir,
        userConfigDir,
        promptsDir,
      });
      expect(loader.getResolvedConfigDir()).toBe(userConfigDir);
    });

    it('should return default dir when nothing else is set', () => {
      const loader = createConfigLoader({
        defaultConfigDir,
        promptsDir,
      });
      expect(loader.getResolvedConfigDir()).toBe(defaultConfigDir);
    });
  });
});

describe('renderTemplate', () => {
  it('should replace single variable', () => {
    expect(renderTemplate('Hello {{name}}', { name: 'World' })).toBe('Hello World');
  });

  it('should replace multiple variables', () => {
    const template = '{{greeting}} {{name}}, welcome to {{place}}';
    const result = renderTemplate(template, {
      greeting: 'Hello',
      name: 'Alice',
      place: 'Galley',
    });
    expect(result).toBe('Hello Alice, welcome to Galley');
  });

  it('should leave unreferenced variables as-is', () => {
    expect(renderTemplate('Hello {{name}}', {})).toBe('Hello {{name}}');
  });

  it('should handle empty template', () => {
    expect(renderTemplate('', { name: 'test' })).toBe('');
  });
});
