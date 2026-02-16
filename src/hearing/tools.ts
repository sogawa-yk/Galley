import crypto from 'node:crypto';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Storage } from '../core/storage.js';
import type { Logger } from '../core/logger.js';
import { GalleyError, wrapToolHandler } from '../core/errors.js';
import {
  CreateSessionArgsSchema,
  SaveAnswerArgsSchema,
  SaveAnswersBatchArgsSchema,
  SessionIdArgsSchema,
  ListSessionsArgsSchema,
  HearingResultSchema,
} from '../core/schema.js';
import type { Session } from '../types/session.js';
import type { HearingResult } from '../types/hearing.js';

const CATEGORY_FIELD_MAP: Record<string, string[]> = {
  project_overview: ['project_overview'],
  scale: ['requirements', 'scale'],
  traffic: ['requirements', 'traffic'],
  database: ['requirements', 'database'],
  network: ['requirements', 'network'],
  security: ['requirements', 'security'],
  availability: ['requirements', 'availability'],
  performance: ['requirements', 'performance'],
  operations: ['requirements', 'operations'],
  budget_schedule: ['requirements', 'budget_schedule'],
};

async function readSession(storage: Storage, sessionId: string): Promise<Session> {
  return storage.readJson<Session>(`sessions/${sessionId}/session.json`);
}

async function readHearingResult(storage: Storage, sessionId: string): Promise<HearingResult> {
  return storage.readJson<HearingResult>(`sessions/${sessionId}/hearing-result.json`);
}

function applyAnswer(
  hearingResult: HearingResult,
  category: string,
  questionId: string,
  value: string | number | boolean,
  source: string,
  estimation?: { confidence_label: string; reasoning: string; source_info?: string },
): void {
  const fieldPath = CATEGORY_FIELD_MAP[category];
  if (!fieldPath) {
    throw new GalleyError('VALIDATION_ERROR', `Unknown category: ${category}`);
  }

  const answeredItem: Record<string, unknown> = { value, source };
  if (estimation) {
    answeredItem['estimation'] = estimation;
  }

  // Navigate the nested path dynamically
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let target = hearingResult as Record<string, any>;
  for (const field of fieldPath) {
    if (target[field] === undefined || target[field] === null) {
      target[field] = {};
    }
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    target = target[field];
  }
  target[questionId] = answeredItem;
}

export function registerHearingTools(
  server: McpServer,
  storage: Storage,
  logger: Logger,
): void {
  // create_session
  server.registerTool('create_session', {
    description: '新しいヒアリングセッションを作成します',
    inputSchema: CreateSessionArgsSchema.shape,
  }, wrapToolHandler(async (args) => {
    const parsed = CreateSessionArgsSchema.parse(args);
    const sessionId = crypto.randomUUID();
    const now = new Date().toISOString();

    const session: Session = {
      session_id: sessionId,
      created_at: now,
      updated_at: now,
      status: 'in_progress',
      project_description: parsed.project_description,
    };

    const hearingResult: HearingResult = {
      metadata: {
        hearing_id: sessionId,
        created_at: now,
        version: '1.0.0',
        status: 'in_progress',
      },
      project_overview: {
        description: parsed.project_description,
      },
      requirements: {},
    };

    await storage.writeJson(`sessions/${sessionId}/session.json`, session);
    await storage.writeJson(`sessions/${sessionId}/hearing-result.json`, hearingResult);

    server.sendResourceListChanged();
    const slog = logger.forSession(sessionId, storage, 'create_session');
    slog.info(`Session created: ${sessionId}`);

    return {
      content: [{ type: 'text', text: JSON.stringify({ session_id: sessionId, created_at: now }) }],
    };
  }, logger));

  // list_sessions
  server.registerTool('list_sessions', {
    description: 'セッション一覧を取得します',
    inputSchema: ListSessionsArgsSchema.shape,
  }, wrapToolHandler(async (args) => {
    const parsed = ListSessionsArgsSchema.parse(args);
    const dirs = await storage.listDirs('sessions');
    const sessions = [];

    for (const dir of dirs) {
      try {
        const session = await readSession(storage, dir);
        if (!parsed.status || session.status === parsed.status) {
          sessions.push({
            session_id: session.session_id,
            project_description: session.project_description,
            status: session.status,
            created_at: session.created_at,
            updated_at: session.updated_at,
          });
        }
      } catch {
        // Skip invalid sessions
      }
    }

    sessions.sort((a, b) => b.created_at.localeCompare(a.created_at));

    return {
      content: [{ type: 'text', text: JSON.stringify(sessions, null, 2) }],
    };
  }, logger));

  // delete_session
  server.registerTool('delete_session', {
    description: 'セッションを削除します',
    inputSchema: SessionIdArgsSchema.shape,
  }, wrapToolHandler(async (args) => {
    const parsed = SessionIdArgsSchema.parse(args);
    const sessionDir = `sessions/${parsed.session_id}`;

    if (!(await storage.exists(`${sessionDir}/session.json`))) {
      throw new GalleyError('SESSION_NOT_FOUND', `Session not found: ${parsed.session_id}`);
    }

    await storage.removeDir(sessionDir);
    await storage.removeDir(`output/${parsed.session_id}`);

    server.sendResourceListChanged();
    const slog = logger.forSession(parsed.session_id, storage, 'delete_session');
    slog.info(`Session deleted: ${parsed.session_id}`);

    return {
      content: [{ type: 'text', text: JSON.stringify({ deleted: true, session_id: parsed.session_id }) }],
    };
  }, logger));

  // save_answer
  server.registerTool('save_answer', {
    description: 'ヒアリングの回答を1件保存します',
    inputSchema: SaveAnswerArgsSchema.shape,
  }, wrapToolHandler(async (args) => {
    const parsed = SaveAnswerArgsSchema.parse(args);
    const session = await readSession(storage, parsed.session_id);

    if (session.status !== 'in_progress') {
      throw new GalleyError('INVALID_SESSION_STATUS', `Session is ${session.status}, cannot save answers`);
    }

    const hearingResult = await readHearingResult(storage, parsed.session_id);
    applyAnswer(hearingResult, parsed.category, parsed.question_id, parsed.value, parsed.source, parsed.estimation);
    hearingResult.metadata.updated_at = new Date().toISOString();

    await storage.writeJson(`sessions/${parsed.session_id}/hearing-result.json`, hearingResult);

    session.updated_at = new Date().toISOString();
    await storage.writeJson(`sessions/${parsed.session_id}/session.json`, session);

    return {
      content: [{ type: 'text', text: JSON.stringify({ saved: true, question_id: parsed.question_id, category: parsed.category }) }],
    };
  }, logger));

  // save_answers_batch
  server.registerTool('save_answers_batch', {
    description: 'ヒアリングの回答を一括保存します',
    inputSchema: SaveAnswersBatchArgsSchema.shape,
  }, wrapToolHandler(async (args) => {
    const parsed = SaveAnswersBatchArgsSchema.parse(args);
    const session = await readSession(storage, parsed.session_id);

    if (session.status !== 'in_progress') {
      throw new GalleyError('INVALID_SESSION_STATUS', `Session is ${session.status}, cannot save answers`);
    }

    const hearingResult = await readHearingResult(storage, parsed.session_id);

    for (const answer of parsed.answers) {
      applyAnswer(hearingResult, answer.category, answer.question_id, answer.value, answer.source, answer.estimation);
    }
    hearingResult.metadata.updated_at = new Date().toISOString();

    await storage.writeJson(`sessions/${parsed.session_id}/hearing-result.json`, hearingResult);

    session.updated_at = new Date().toISOString();
    await storage.writeJson(`sessions/${parsed.session_id}/session.json`, session);

    return {
      content: [{ type: 'text', text: JSON.stringify({ saved: true, count: parsed.answers.length }) }],
    };
  }, logger));

  // complete_hearing
  server.registerTool('complete_hearing', {
    description: 'ヒアリングを完了します',
    inputSchema: SessionIdArgsSchema.shape,
  }, wrapToolHandler(async (args) => {
    const parsed = SessionIdArgsSchema.parse(args);
    const session = await readSession(storage, parsed.session_id);

    if (session.status !== 'in_progress') {
      throw new GalleyError('INVALID_SESSION_STATUS', `Session is already ${session.status}`);
    }

    const hearingResult = await readHearingResult(storage, parsed.session_id);
    hearingResult.metadata.status = 'completed';
    hearingResult.metadata.updated_at = new Date().toISOString();
    await storage.writeJson(`sessions/${parsed.session_id}/hearing-result.json`, hearingResult);

    session.status = 'completed';
    session.updated_at = new Date().toISOString();
    await storage.writeJson(`sessions/${parsed.session_id}/session.json`, session);

    // Count answered/unanswered categories
    const requirements = hearingResult.requirements;
    const categories = Object.keys(CATEGORY_FIELD_MAP).filter((c) => c !== 'project_overview');
    let answered = 0;
    for (const cat of categories) {
      const reqKey = cat as keyof typeof requirements;
      const data = requirements[reqKey];
      if (data && Object.keys(data).length > 0) {
        answered++;
      }
    }

    const summary = {
      total_categories: categories.length,
      answered_categories: answered,
      unanswered_categories: categories.length - answered,
    };

    return {
      content: [{ type: 'text', text: JSON.stringify({ session_id: parsed.session_id, status: 'completed', summary }) }],
    };
  }, logger));

  // get_hearing_result
  server.registerTool('get_hearing_result', {
    description: 'ヒアリング結果を取得します',
    inputSchema: SessionIdArgsSchema.shape,
  }, wrapToolHandler(async (args) => {
    const parsed = SessionIdArgsSchema.parse(args);
    const raw = await storage.readJson<unknown>(`sessions/${parsed.session_id}/hearing-result.json`);
    const hearingResult = HearingResultSchema.parse(raw);

    return {
      content: [{ type: 'text', text: JSON.stringify(hearingResult, null, 2) }],
    };
  }, logger));
}

// Export for testing
export { CATEGORY_FIELD_MAP, applyAnswer };
