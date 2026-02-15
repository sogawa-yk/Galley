import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { ConfigLoader } from '../core/config.js';
import { renderTemplate } from '../core/config.js';

export function registerDeployPrompts(
  server: McpServer,
  configLoader: ConfigLoader,
): void {
  server.registerPrompt('deploy-to-rm', {
    description: 'Terraformファイルを OCI Resource Manager にデプロイするプロンプト',
    argsSchema: {
      session_id: z.string().describe('デプロイ対象のセッションID'),
    },
  }, async (args) => {
    const template = await configLoader.loadPromptTemplate('deploy-to-rm.md');
    const content = renderTemplate(template, { session_id: args.session_id });
    return {
      messages: [{ role: 'user', content: { type: 'text', text: content } }],
    };
  });
}
