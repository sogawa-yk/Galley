import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { createLogger } from './core/logger.js';
import type { LogLevel } from './core/logger.js';
import { createStorage } from './core/storage.js';
import { createConfigLoader } from './core/config.js';
import { createGalleyServer } from './server.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PACKAGE_ROOT = path.resolve(__dirname, '..');

async function main(): Promise<void> {
  const { values } = parseArgs({
    options: {
      'data-dir': { type: 'string', default: path.join(os.homedir(), '.galley') },
      'config-dir': { type: 'string' },
      'log-level': { type: 'string', default: 'info' },
    },
  });

  const dataDir = values['data-dir'] ?? path.join(os.homedir(), '.galley');
  const logLevel = values['log-level'] ?? 'info';

  const logger = createLogger({ level: logLevel as LogLevel });
  const storage = createStorage({ baseDir: dataDir });
  await storage.initDataDir();

  const configLoader = createConfigLoader({
    defaultConfigDir: path.join(PACKAGE_ROOT, 'config'),
    userConfigDir: path.join(dataDir, 'config'),
    overrideConfigDir: values['config-dir'],
    promptsDir: path.join(PACKAGE_ROOT, 'prompts'),
  });

  const server = createGalleyServer({ storage, configLoader, logger });
  logger.setServer(server);

  const transport = new StdioServerTransport();
  await server.connect(transport);

  logger.info('Galley MCP server started');
}

main().catch((error: unknown) => {
  console.error('Failed to start Galley MCP server:', error);
  process.exit(1);
});
