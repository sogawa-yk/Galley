import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Storage } from '../core/storage.js';

export function registerDeployResources(
  _server: McpServer,
  _storage: Storage,
): void {
  // No deploy-specific resources for now.
  // Future: expose deploy state as a resource.
}
