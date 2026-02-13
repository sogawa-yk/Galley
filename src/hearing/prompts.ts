import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { ConfigLoader } from '../core/config.js';
import { renderTemplate } from '../core/config.js';

export function registerHearingPrompts(
  server: McpServer,
  configLoader: ConfigLoader,
): void {
  server.registerPrompt('start-hearing', {
    description: 'ヒアリングを開始するプロンプト',
    argsSchema: {
      project_description: z.string().describe('案件の概要'),
    },
  }, async (args) => {
    const template = await configLoader.loadPromptTemplate('start-hearing.md');
    const content = renderTemplate(template, { project_description: args.project_description });
    return {
      messages: [{ role: 'user', content: { type: 'text', text: content } }],
    };
  });

  server.registerPrompt('resume-hearing', {
    description: '中断したヒアリングを再開するプロンプト',
    argsSchema: {
      session_id: z.string().describe('再開するセッションID'),
    },
  }, async (args) => {
    const template = await configLoader.loadPromptTemplate('resume-hearing.md');
    const content = renderTemplate(template, { session_id: args.session_id });
    return {
      messages: [{ role: 'user', content: { type: 'text', text: content } }],
    };
  });
}
