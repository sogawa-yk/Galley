import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Storage } from '../core/storage.js';
import type { Logger } from '../core/logger.js';
import { GalleyError, wrapToolHandler } from '../core/errors.js';
import {
  SaveArchitectureArgsSchema,
  ExportMermaidArgsSchema,
  ExportIacArgsSchema,
  ExportAllArgsSchema,
  SessionIdArgsSchema,
} from '../core/schema.js';
import type { HearingResult } from '../types/hearing.js';
import type { ArchitectureOutput } from '../types/architecture.js';

function buildSummaryMarkdown(
  hearingResult: HearingResult,
  architecture?: ArchitectureOutput,
): string {
  const lines: string[] = ['# 要件サマリー', ''];

  lines.push('## 案件概要', '');
  lines.push(`- ${hearingResult.project_overview.description}`);
  if (hearingResult.project_overview.industry) {
    lines.push(`- 業種: ${hearingResult.project_overview.industry.value}`);
  }
  if (hearingResult.project_overview.project_type) {
    lines.push(`- 案件種別: ${hearingResult.project_overview.project_type.value}`);
  }
  lines.push('');

  lines.push('## 要件一覧', '');
  const requirements = hearingResult.requirements;
  for (const [category, data] of Object.entries(requirements)) {
    if (!data || Object.keys(data).length === 0) continue;
    lines.push(`### ${category}`, '');
    for (const [key, item] of Object.entries(data as Record<string, { value: unknown; source: string; estimation?: { reasoning: string } }>)) {
      let prefix: string;
      if (item.source === 'user_selected' || item.source === 'user_free_text') {
        prefix = '✅';
      } else if (item.source === 'estimated') {
        prefix = '🔶';
      } else {
        prefix = '⚠️';
      }
      let line = `- ${prefix} **${key}**: ${String(item.value)}`;
      if (item.source === 'estimated' && item.estimation) {
        line += ` _(推測: ${item.estimation.reasoning})_`;
      }
      lines.push(line);
    }
    lines.push('');
  }

  if (architecture) {
    lines.push('## アーキテクチャ', '');
    lines.push('### コンポーネント', '');
    lines.push('| カテゴリ | サービス | 目的 | 選定理由 |');
    lines.push('|---------|---------|------|---------|');
    for (const comp of architecture.components) {
      lines.push(`| ${comp.category} | ${comp.service_name} | ${comp.purpose} | ${comp.reason} |`);
    }
    lines.push('');

    if (architecture.warnings.length > 0) {
      lines.push('### 警告', '');
      for (const w of architecture.warnings) {
        const icon = w.severity === 'error' ? '🔴' : w.severity === 'warning' ? '🟡' : 'ℹ️';
        lines.push(`- ${icon} **${w.type}**: ${w.message}`);
      }
      lines.push('');
    }
  }

  return lines.join('\n');
}

export function registerGenerateTools(
  server: McpServer,
  storage: Storage,
  logger: Logger,
): void {
  // save_architecture
  server.registerTool('save_architecture', {
    description: 'アーキテクチャ設計を保存します',
    inputSchema: SaveArchitectureArgsSchema.shape,
  }, wrapToolHandler(async (args) => {
    const parsed = SaveArchitectureArgsSchema.parse(args);

    if (!(await storage.exists(`sessions/${parsed.session_id}/session.json`))) {
      throw new GalleyError('SESSION_NOT_FOUND', `Session not found: ${parsed.session_id}`);
    }

    const architectureOutput: ArchitectureOutput = {
      session_id: parsed.session_id,
      components: parsed.components,
      decisions: parsed.decisions,
      warnings: parsed.warnings,
    };

    await storage.writeJson(`sessions/${parsed.session_id}/architecture.json`, architectureOutput);
    logger.info(`Architecture saved for session: ${parsed.session_id}`);

    return {
      content: [{ type: 'text', text: JSON.stringify({ saved: true, session_id: parsed.session_id, component_count: parsed.components.length }) }],
    };
  }, logger));

  // export_summary
  server.registerTool('export_summary', {
    description: '要件サマリーをMarkdownで出力します',
    inputSchema: SessionIdArgsSchema.shape,
  }, wrapToolHandler(async (args) => {
    const parsed = SessionIdArgsSchema.parse(args);
    const hearingResult = await storage.readJson<HearingResult>(`sessions/${parsed.session_id}/hearing-result.json`);

    let architecture: ArchitectureOutput | undefined;
    try {
      architecture = await storage.readJson<ArchitectureOutput>(`sessions/${parsed.session_id}/architecture.json`);
    } catch {
      // architecture.json might not exist
    }

    const markdown = buildSummaryMarkdown(hearingResult, architecture);
    const filePath = `output/${parsed.session_id}/summary.md`;
    await storage.writeText(filePath, markdown);

    return {
      content: [{ type: 'text', text: JSON.stringify({ file_path: filePath }) }],
    };
  }, logger));

  // export_mermaid
  server.registerTool('export_mermaid', {
    description: '構成図をMermaidファイルで出力します',
    inputSchema: ExportMermaidArgsSchema.shape,
  }, wrapToolHandler(async (args) => {
    const parsed = ExportMermaidArgsSchema.parse(args);
    const filePath = `output/${parsed.session_id}/architecture.mmd`;
    await storage.writeText(filePath, parsed.mermaid_code);

    return {
      content: [{ type: 'text', text: JSON.stringify({ file_path: filePath }) }],
    };
  }, logger));

  // export_iac
  server.registerTool('export_iac', {
    description: 'IaCテンプレートを出力します',
    inputSchema: ExportIacArgsSchema.shape,
  }, wrapToolHandler(async (args) => {
    const parsed = ExportIacArgsSchema.parse(args);
    const filePaths: string[] = [];

    for (const file of parsed.files) {
      storage.validateFilename(file.name);
      const filePath = `output/${parsed.session_id}/terraform/${file.name}`;
      await storage.writeText(filePath, file.content);
      filePaths.push(filePath);
    }

    return {
      content: [{ type: 'text', text: JSON.stringify({ file_paths: filePaths }) }],
    };
  }, logger));

  // export_all
  server.registerTool('export_all', {
    description: '全成果物を一括出力します',
    inputSchema: ExportAllArgsSchema.shape,
  }, wrapToolHandler(async (args) => {
    const parsed = ExportAllArgsSchema.parse(args);
    const files: string[] = [];

    // Always export summary
    const hearingResult = await storage.readJson<HearingResult>(`sessions/${parsed.session_id}/hearing-result.json`);
    let architecture: ArchitectureOutput | undefined;
    try {
      architecture = await storage.readJson<ArchitectureOutput>(`sessions/${parsed.session_id}/architecture.json`);
    } catch {
      // architecture.json might not exist
    }

    const summaryPath = `output/${parsed.session_id}/summary.md`;
    const markdown = buildSummaryMarkdown(hearingResult, architecture);
    await storage.writeText(summaryPath, markdown);
    files.push(summaryPath);

    // Export mermaid if provided
    if (parsed.mermaid_code) {
      const mermaidPath = `output/${parsed.session_id}/architecture.mmd`;
      await storage.writeText(mermaidPath, parsed.mermaid_code);
      files.push(mermaidPath);
    }

    // Export IaC files if provided
    if (parsed.iac_files) {
      for (const file of parsed.iac_files) {
        storage.validateFilename(file.name);
        const filePath = `output/${parsed.session_id}/terraform/${file.name}`;
        await storage.writeText(filePath, file.content);
        files.push(filePath);
      }
    }

    return {
      content: [{ type: 'text', text: JSON.stringify({ output_dir: `output/${parsed.session_id}/`, files }) }],
    };
  }, logger));
}

export { buildSummaryMarkdown };
