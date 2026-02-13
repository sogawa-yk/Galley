import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { ConfigLoader } from '../core/config.js';
import { renderTemplate } from '../core/config.js';

export function registerGeneratePrompts(
  server: McpServer,
  configLoader: ConfigLoader,
): void {
  server.registerPrompt('generate-architecture', {
    description: 'ヒアリング結果からOCIアーキテクチャを生成するプロンプト',
    argsSchema: {
      session_id: z.string().describe('アーキテクチャを生成するセッションID'),
    },
  }, async (args) => {
    const template = await configLoader.loadPromptTemplate('generate-architecture.md');
    const content = renderTemplate(template, { session_id: args.session_id });
    return {
      messages: [{ role: 'user', content: { type: 'text', text: content } }],
    };
  });
}
