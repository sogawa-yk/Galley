import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { ConfigLoader } from '../core/config.js';
import {
  OciServicesConfigSchema,
  OciArchitecturesConfigSchema,
  OciTerraformConfigSchema,
} from '../core/schema.js';

export function registerGenerateResources(
  server: McpServer,
  configLoader: ConfigLoader,
): void {
  let cachedServices: string | undefined;
  let cachedArchitectures: string | undefined;
  let cachedTerraform: string | undefined;

  server.registerResource('oci-services', 'galley://references/oci-services', {
    description: 'OCIサービスカタログ',
    mimeType: 'application/json',
  }, async (uri) => {
    if (!cachedServices) {
      const data = await configLoader.loadConfig('oci-services.yaml', OciServicesConfigSchema);
      cachedServices = JSON.stringify(data, null, 2);
    }
    return {
      contents: [{ uri: uri.href, text: cachedServices, mimeType: 'application/json' }],
    };
  });

  server.registerResource('oci-architectures', 'galley://references/oci-architectures', {
    description: 'OCIリファレンスアーキテクチャ',
    mimeType: 'application/json',
  }, async (uri) => {
    if (!cachedArchitectures) {
      const data = await configLoader.loadConfig('oci-architectures.yaml', OciArchitecturesConfigSchema);
      cachedArchitectures = JSON.stringify(data, null, 2);
    }
    return {
      contents: [{ uri: uri.href, text: cachedArchitectures, mimeType: 'application/json' }],
    };
  });

  server.registerResource('oci-terraform', 'galley://references/oci-terraform', {
    description: 'OCI Terraformリソース定義',
    mimeType: 'application/json',
  }, async (uri) => {
    if (!cachedTerraform) {
      const data = await configLoader.loadConfig('oci-terraform.yaml', OciTerraformConfigSchema);
      cachedTerraform = JSON.stringify(data, null, 2);
    }
    return {
      contents: [{ uri: uri.href, text: cachedTerraform, mimeType: 'application/json' }],
    };
  });
}
