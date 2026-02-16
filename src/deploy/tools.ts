import os from 'node:os';
import path from 'node:path';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Storage } from '../core/storage.js';
import type { Logger } from '../core/logger.js';
import type { OciCli } from '../core/oci-cli.js';
import { GalleyError, wrapToolHandler } from '../core/errors.js';
import {
  CheckOciCliArgsSchema,
  CreateRmStackArgsSchema,
  RunRmPlanArgsSchema,
  RunRmApplyArgsSchema,
  GetRmJobStatusArgsSchema,
  DeployStateSchema,
} from '../core/schema.js';
import type { DeployState, RmJobRecord } from '../types/deploy.js';

function deployStatePath(sessionId: string): string {
  return `sessions/${sessionId}/deploy-state.json`;
}

async function loadDeployState(storage: Storage, sessionId: string): Promise<DeployState> {
  const p = deployStatePath(sessionId);
  if (!(await storage.exists(p))) {
    throw new GalleyError('DEPLOY_ERROR', `No deploy state found for session: ${sessionId}. Run create_rm_stack first.`);
  }
  const raw = await storage.readJson<unknown>(p);
  return DeployStateSchema.parse(raw);
}

async function saveDeployState(storage: Storage, state: DeployState): Promise<void> {
  state.updated_at = new Date().toISOString();
  await storage.writeJson(deployStatePath(state.session_id), state);
}

function findLatestJob(state: DeployState, jobType: 'plan' | 'apply'): RmJobRecord | undefined {
  return [...state.jobs].reverse().find((j) => j.job_type === jobType);
}

export function registerDeployTools(
  server: McpServer,
  storage: Storage,
  logger: Logger,
  ociCli: OciCli,
): void {
  // check_oci_cli
  server.registerTool('check_oci_cli', {
    description: 'OCI CLIとzipコマンドの利用可否を確認します',
    inputSchema: CheckOciCliArgsSchema.shape,
  }, wrapToolHandler(async () => {
    const results: { oci_cli?: string; zip?: string; errors: string[] } = { errors: [] };

    try {
      results.oci_cli = await ociCli.checkVersion();
    } catch (error) {
      if (error instanceof GalleyError) {
        results.errors.push(`oci: ${error.message}`);
      } else {
        results.errors.push('oci: unknown error');
      }
    }

    try {
      results.zip = await ociCli.checkZip();
    } catch (error) {
      if (error instanceof GalleyError) {
        results.errors.push(`zip: ${error.message}`);
      } else {
        results.errors.push('zip: unknown error');
      }
    }

    return {
      content: [{ type: 'text', text: JSON.stringify(results) }],
    };
  }, logger));

  // create_rm_stack
  server.registerTool('create_rm_stack', {
    description: 'エクスポート済みTerraformファイルをZIP化してOCI Resource Managerスタックを作成します',
    inputSchema: CreateRmStackArgsSchema.shape,
  }, wrapToolHandler(async (args) => {
    const parsed = CreateRmStackArgsSchema.parse(args);
    const sessionId = parsed.session_id;

    // Verify session exists
    if (!(await storage.exists(`sessions/${sessionId}/session.json`))) {
      throw new GalleyError('SESSION_NOT_FOUND', `Session not found: ${sessionId}`);
    }

    // Verify terraform files are exported
    const terraformDir = `output/${sessionId}/terraform`;
    if (!(await storage.exists(terraformDir))) {
      throw new GalleyError('TERRAFORM_NOT_EXPORTED', `Terraform files not exported for session: ${sessionId}. Run export_iac or export_all first.`);
    }

    // Create ZIP from terraform directory
    const terraformAbsDir = storage.validatePath(terraformDir);
    const tmpZipPath = path.join(os.tmpdir(), `galley-${sessionId.slice(0, 8)}-${Date.now()}.zip`);

    await ociCli.createZip(terraformAbsDir, tmpZipPath);

    // Create RM stack
    const displayName = parsed.display_name ?? `galley-${sessionId.slice(0, 8)}`;
    const stackArgs: Record<string, string> = {
      'compartment-id': parsed.compartment_id,
      'config-source': tmpZipPath,
      'display-name': displayName,
    };
    if (parsed.terraform_version) {
      stackArgs['terraform-version'] = parsed.terraform_version;
    }

    const result = await ociCli.execute(
      ['resource-manager', 'stack', 'create', '--config-source-type', 'ZIP_UPLOAD'],
      stackArgs,
      { waitForState: 'ACTIVE', timeoutMs: 60_000 },
    );

    const data = result.parsed as { data?: { id?: string } } | undefined;
    const stackId = data?.data?.id;
    if (!stackId) {
      throw new GalleyError('DEPLOY_ERROR', 'Failed to extract stack ID from OCI CLI response');
    }

    // Save deploy state
    const now = new Date().toISOString();
    const state: DeployState = {
      session_id: sessionId,
      stack_id: stackId,
      stack_display_name: displayName,
      compartment_id: parsed.compartment_id,
      terraform_version: parsed.terraform_version,
      jobs: [],
      created_at: now,
      updated_at: now,
    };
    await saveDeployState(storage, state);

    const slog = logger.forSession(sessionId, storage, 'create_rm_stack');
    slog.info(`RM stack created: ${stackId}`, { sessionId, displayName });

    return {
      content: [{ type: 'text', text: JSON.stringify({ stack_id: stackId, display_name: displayName }) }],
    };
  }, logger));

  // run_rm_plan
  server.registerTool('run_rm_plan', {
    description: 'Resource Managerスタックに対してPlanジョブを実行します（非同期）',
    inputSchema: RunRmPlanArgsSchema.shape,
  }, wrapToolHandler(async (args) => {
    const parsed = RunRmPlanArgsSchema.parse(args);
    const sessionId = parsed.session_id;
    const state = await loadDeployState(storage, sessionId);

    const stackId = parsed.stack_id ?? state.stack_id;
    if (!stackId) {
      throw new GalleyError('DEPLOY_ERROR', 'No stack_id available. Provide stack_id or run create_rm_stack first.');
    }

    const result = await ociCli.execute(
      ['resource-manager', 'job', 'create'],
      {
        'stack-id': stackId,
        operation: 'PLAN',
      },
    );

    const data = result.parsed as { data?: { id?: string; 'lifecycle-state'?: string } } | undefined;
    const jobId = data?.data?.id;
    if (!jobId) {
      throw new GalleyError('DEPLOY_ERROR', 'Failed to extract job ID from OCI CLI response');
    }

    const jobRecord: RmJobRecord = {
      job_id: jobId,
      job_type: 'plan',
      status: data?.data?.['lifecycle-state'] ?? 'ACCEPTED',
      created_at: new Date().toISOString(),
    };
    state.jobs.push(jobRecord);
    await saveDeployState(storage, state);

    const slog = logger.forSession(sessionId, storage, 'run_rm_plan');
    slog.info(`Plan job created: ${jobId}`, { sessionId, stackId });

    return {
      content: [{ type: 'text', text: JSON.stringify({ job_id: jobId, status: jobRecord.status }) }],
    };
  }, logger));

  // run_rm_apply
  server.registerTool('run_rm_apply', {
    description: 'Resource Managerスタックに対してApplyジョブを実行します（非同期）',
    inputSchema: RunRmApplyArgsSchema.shape,
  }, wrapToolHandler(async (args) => {
    const parsed = RunRmApplyArgsSchema.parse(args);
    const sessionId = parsed.session_id;
    const state = await loadDeployState(storage, sessionId);

    const stackId = parsed.stack_id ?? state.stack_id;
    if (!stackId) {
      throw new GalleyError('DEPLOY_ERROR', 'No stack_id available. Provide stack_id or run create_rm_stack first.');
    }

    const jobArgs: Record<string, string> = {
      'stack-id': stackId,
      operation: 'APPLY',
      'execution-plan-strategy': parsed.execution_plan_strategy,
    };

    if (parsed.execution_plan_strategy === 'FROM_PLAN_JOB_ID') {
      const planJobId = parsed.plan_job_id ?? findLatestJob(state, 'plan')?.job_id;
      if (!planJobId) {
        throw new GalleyError('DEPLOY_ERROR', 'No plan_job_id available. Provide plan_job_id or run run_rm_plan first.');
      }
      jobArgs['execution-plan-job-id'] = planJobId;
    }

    const result = await ociCli.execute(
      ['resource-manager', 'job', 'create'],
      jobArgs,
    );

    const data = result.parsed as { data?: { id?: string; 'lifecycle-state'?: string } } | undefined;
    const jobId = data?.data?.id;
    if (!jobId) {
      throw new GalleyError('DEPLOY_ERROR', 'Failed to extract job ID from OCI CLI response');
    }

    const jobRecord: RmJobRecord = {
      job_id: jobId,
      job_type: 'apply',
      status: data?.data?.['lifecycle-state'] ?? 'ACCEPTED',
      created_at: new Date().toISOString(),
    };
    state.jobs.push(jobRecord);
    await saveDeployState(storage, state);

    const slog = logger.forSession(sessionId, storage, 'run_rm_apply');
    slog.info(`Apply job created: ${jobId}`, { sessionId, stackId });

    return {
      content: [{ type: 'text', text: JSON.stringify({ job_id: jobId, status: jobRecord.status }) }],
    };
  }, logger));

  // get_rm_job_status
  server.registerTool('get_rm_job_status', {
    description: 'Resource Managerジョブの状態とオプションでログを取得します',
    inputSchema: GetRmJobStatusArgsSchema.shape,
  }, wrapToolHandler(async (args) => {
    const parsed = GetRmJobStatusArgsSchema.parse(args);
    const sessionId = parsed.session_id;
    const state = await loadDeployState(storage, sessionId);

    // Get job status
    const result = await ociCli.execute(
      ['resource-manager', 'job', 'get'],
      { 'job-id': parsed.job_id },
    );

    const data = result.parsed as { data?: { id?: string; 'lifecycle-state'?: string; operation?: string } } | undefined;
    const status = data?.data?.['lifecycle-state'] ?? 'UNKNOWN';

    // Update job record in deploy state
    const jobRecord = state.jobs.find((j) => j.job_id === parsed.job_id);
    if (jobRecord) {
      jobRecord.status = status;
      jobRecord.updated_at = new Date().toISOString();
      await saveDeployState(storage, state);
    }

    const response: Record<string, unknown> = {
      job_id: parsed.job_id,
      status,
      operation: data?.data?.operation,
    };

    // Optionally fetch logs
    if (parsed.include_logs) {
      try {
        const logsResult = await ociCli.execute(
          ['resource-manager', 'job', 'get-job-logs'],
          { 'job-id': parsed.job_id },
        );
        const logsData = logsResult.parsed as { data?: Array<{ message?: string }> } | undefined;
        if (logsData?.data) {
          response.logs = logsData.data.map((entry) => entry.message ?? '').join('\n');
        }
      } catch (error) {
        const slog = logger.forSession(sessionId, storage, 'get_rm_job_status');
        slog.warning('Failed to fetch job logs', error);
        response.logs_error = 'Failed to fetch logs';
      }
    }

    return {
      content: [{ type: 'text', text: JSON.stringify(response) }],
    };
  }, logger));
}
