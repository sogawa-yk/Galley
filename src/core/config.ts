import fs from 'node:fs/promises';
import path from 'node:path';
import { parse as parseYaml } from 'yaml';
import type { ZodSchema } from 'zod';
import { GalleyError } from './errors.js';

export interface ConfigLoaderOptions {
  defaultConfigDir: string;
  userConfigDir?: string;
  overrideConfigDir?: string;
  promptsDir: string;
}

export interface ConfigLoader {
  loadConfig<T>(filename: string, schema: ZodSchema<T>): Promise<T>;
  loadPromptTemplate(filename: string): Promise<string>;
  getResolvedConfigDir(): string;
}

export function createConfigLoader(options: ConfigLoaderOptions): ConfigLoader {
  async function findConfigFile(filename: string): Promise<string> {
    if (options.overrideConfigDir) {
      const overridePath = path.join(options.overrideConfigDir, filename);
      if (await fileExists(overridePath)) return overridePath;
    }
    if (options.userConfigDir) {
      const userPath = path.join(options.userConfigDir, filename);
      if (await fileExists(userPath)) return userPath;
    }
    const defaultPath = path.join(options.defaultConfigDir, filename);
    if (await fileExists(defaultPath)) return defaultPath;
    throw new GalleyError('CONFIG_LOAD_ERROR', `Config file not found: ${filename}`);
  }

  async function fileExists(filePath: string): Promise<boolean> {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  return {
    async loadConfig<T>(filename: string, schema: ZodSchema<T>): Promise<T> {
      const filePath = await findConfigFile(filename);
      try {
        const content = await fs.readFile(filePath, 'utf-8');
        const parsed = parseYaml(content) as unknown;
        const result = schema.safeParse(parsed);
        if (!result.success) {
          throw new GalleyError(
            'CONFIG_LOAD_ERROR',
            `Validation failed for ${filename}: ${result.error.message}`,
          );
        }
        return result.data;
      } catch (error) {
        if (error instanceof GalleyError) throw error;
        throw new GalleyError('CONFIG_LOAD_ERROR', `Failed to load config: ${filename}`, error);
      }
    },

    async loadPromptTemplate(filename: string): Promise<string> {
      const filePath = path.join(options.promptsDir, filename);
      try {
        return await fs.readFile(filePath, 'utf-8');
      } catch (error) {
        throw new GalleyError(
          'CONFIG_LOAD_ERROR',
          `Prompt template not found: ${filename}`,
          error,
        );
      }
    },

    getResolvedConfigDir(): string {
      return options.overrideConfigDir ?? options.userConfigDir ?? options.defaultConfigDir;
    },
  };
}

export function renderTemplate(template: string, variables: Record<string, string>): string {
  return Object.entries(variables).reduce(
    (result, [key, value]) => result.replaceAll(`{{${key}}}`, value),
    template,
  );
}
