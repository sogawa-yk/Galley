import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { ConfigLoader } from '../core/config.js';
import type { Storage } from '../core/storage.js';
import { HearingQuestionsConfigSchema, HearingFlowConfigSchema } from '../core/schema.js';

export function registerHearingResources(
  server: McpServer,
  configLoader: ConfigLoader,
  storage: Storage,
): void {
  let cachedQuestions: string | undefined;
  let cachedFlow: string | undefined;
  let cachedSchema: string | undefined;

  server.registerResource('hearing-questions', 'galley://templates/hearing-questions', {
    description: 'ヒアリング質問テンプレート',
    mimeType: 'application/json',
  }, async (uri) => {
    if (!cachedQuestions) {
      const data = await configLoader.loadConfig('hearing-questions.yaml', HearingQuestionsConfigSchema);
      cachedQuestions = JSON.stringify(data, null, 2);
    }
    return {
      contents: [{ uri: uri.href, text: cachedQuestions, mimeType: 'application/json' }],
    };
  });

  server.registerResource('hearing-flow', 'galley://templates/hearing-flow', {
    description: 'ヒアリングフロー定義',
    mimeType: 'application/json',
  }, async (uri) => {
    if (!cachedFlow) {
      const data = await configLoader.loadConfig('hearing-flow.yaml', HearingFlowConfigSchema);
      cachedFlow = JSON.stringify(data, null, 2);
    }
    return {
      contents: [{ uri: uri.href, text: cachedFlow, mimeType: 'application/json' }],
    };
  });

  server.registerResource('hearing-result-schema', 'galley://schemas/hearing-result', {
    description: 'ヒアリング結果のJSON Schema',
    mimeType: 'application/json',
  }, async (uri) => {
    if (!cachedSchema) {
      cachedSchema = await configLoader.loadPromptTemplate('../config/hearing-result-schema.json');
    }
    return {
      contents: [{ uri: uri.href, text: cachedSchema, mimeType: 'application/json' }],
    };
  });

  server.registerResource('sessions-list', 'galley://sessions', {
    description: 'セッション一覧',
    mimeType: 'application/json',
  }, async (uri) => {
    const dirs = await storage.listDirs('sessions');
    const sessions = [];
    for (const dir of dirs) {
      try {
        const session = await storage.readJson<Record<string, unknown>>(`sessions/${dir}/session.json`);
        sessions.push(session);
      } catch {
        // Skip invalid sessions
      }
    }
    return {
      contents: [{ uri: uri.href, text: JSON.stringify(sessions, null, 2), mimeType: 'application/json' }],
    };
  });

  const sessionTemplate = new ResourceTemplate('galley://sessions/{session_id}', {
    list: async () => {
      const dirs = await storage.listDirs('sessions');
      return {
        resources: dirs.map((dir) => ({
          uri: `galley://sessions/${dir}`,
          name: `Session ${dir}`,
        })),
      };
    },
  });

  server.registerResource('session-detail', sessionTemplate, {
    description: 'セッション詳細',
    mimeType: 'application/json',
  }, async (uri, variables) => {
    const sessionId = variables.session_id as string;
    const session = await storage.readJson<Record<string, unknown>>(`sessions/${sessionId}/session.json`);
    let hearingResult: Record<string, unknown> | undefined;
    try {
      hearingResult = await storage.readJson<Record<string, unknown>>(`sessions/${sessionId}/hearing-result.json`);
    } catch {
      // hearing-result.json might not exist yet
    }
    const data = { session, hearing_result: hearingResult };
    return {
      contents: [{ uri: uri.href, text: JSON.stringify(data, null, 2), mimeType: 'application/json' }],
    };
  });
}
