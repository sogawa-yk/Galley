import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Storage } from './core/storage.js';
import type { ConfigLoader } from './core/config.js';
import type { Logger } from './core/logger.js';
import type { OciCli } from './core/oci-cli.js';
import { createOciCli } from './core/oci-cli.js';
import { registerHearingResources } from './hearing/resources.js';
import { registerHearingTools } from './hearing/tools.js';
import { registerHearingPrompts } from './hearing/prompts.js';
import { registerGenerateResources } from './generate/resources.js';
import { registerGenerateTools } from './generate/tools.js';
import { registerGeneratePrompts } from './generate/prompts.js';
import { registerDeployResources } from './deploy/resources.js';
import { registerDeployTools } from './deploy/tools.js';
import { registerDeployPrompts } from './deploy/prompts.js';

export interface ServerDependencies {
  storage: Storage;
  configLoader: ConfigLoader;
  logger: Logger;
  ociCli?: OciCli;
}

export function createGalleyServer(deps: ServerDependencies): McpServer {
  const server = new McpServer(
    { name: 'galley', version: '0.1.0' },
    {
      capabilities: {
        resources: { listChanged: true },
        tools: {},
        prompts: {},
        logging: {},
      },
    },
  );

  registerHearingResources(server, deps.configLoader, deps.storage);
  registerHearingTools(server, deps.storage, deps.logger);
  registerHearingPrompts(server, deps.configLoader);

  registerGenerateResources(server, deps.configLoader);
  registerGenerateTools(server, deps.storage, deps.logger);
  registerGeneratePrompts(server, deps.configLoader);

  const ociCli = deps.ociCli ?? createOciCli(deps.logger);
  registerDeployResources(server, deps.storage);
  registerDeployTools(server, deps.storage, deps.logger, ociCli);
  registerDeployPrompts(server, deps.configLoader);

  return server;
}
