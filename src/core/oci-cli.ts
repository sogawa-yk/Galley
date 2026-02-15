import { execFile as execFileCb } from 'node:child_process';
import { promisify } from 'node:util';
import type { Logger } from './logger.js';
import { GalleyError } from './errors.js';

const execFile = promisify(execFileCb);

export interface OciCliOptions {
  timeoutMs?: number;
  waitForState?: string;
}

export interface OciCliResult {
  stdout: string;
  parsed: unknown;
}

export interface OciCli {
  checkVersion(): Promise<string>;
  checkZip(): Promise<string>;
  execute(subcommand: string[], args: Record<string, string>, options?: OciCliOptions): Promise<OciCliResult>;
  createZip(sourceDir: string, outputPath: string): Promise<void>;
}

export function createOciCli(logger: Logger): OciCli {
  async function runExecFile(
    command: string,
    args: string[],
    options?: { cwd?: string; timeoutMs?: number },
  ): Promise<{ stdout: string; stderr: string }> {
    try {
      const result = await execFile(command, args, {
        cwd: options?.cwd,
        timeout: options?.timeoutMs ?? 120_000,
        maxBuffer: 10 * 1024 * 1024,
      });
      return { stdout: result.stdout, stderr: result.stderr };
    } catch (error) {
      const execError = error as NodeJS.ErrnoException & { stdout?: string; stderr?: string };
      if (execError.code === 'ENOENT') {
        throw new GalleyError(
          'OCI_CLI_NOT_FOUND',
          `Command not found: ${command}. Please install it and ensure it is on your PATH.`,
          error,
        );
      }
      throw new GalleyError(
        'OCI_CLI_ERROR',
        `Command failed: ${command} ${args.join(' ')}\n${execError.stderr ?? execError.message}`,
        error,
      );
    }
  }

  return {
    async checkVersion(): Promise<string> {
      const { stdout } = await runExecFile('oci', ['--version']);
      return stdout.trim();
    },

    async checkZip(): Promise<string> {
      const { stdout } = await runExecFile('zip', ['--version']);
      const firstLine = stdout.split('\n').find((l) => l.trim().length > 0) ?? stdout.trim();
      return firstLine.trim();
    },

    async execute(
      subcommand: string[],
      args: Record<string, string>,
      options?: OciCliOptions,
    ): Promise<OciCliResult> {
      const cliArgs = [...subcommand, '--output', 'json'];

      for (const [key, value] of Object.entries(args)) {
        cliArgs.push(`--${key}`, value);
      }

      if (options?.waitForState) {
        cliArgs.push('--wait-for-state', options.waitForState);
        cliArgs.push('--wait-interval-seconds', '5');
      }

      logger.debug('OCI CLI execute', { args: cliArgs });

      const { stdout } = await runExecFile('oci', cliArgs, {
        timeoutMs: options?.timeoutMs ?? 120_000,
      });

      let parsed: unknown = null;
      try {
        parsed = JSON.parse(stdout);
      } catch {
        // Some commands may not return JSON
      }

      return { stdout, parsed };
    },

    async createZip(sourceDir: string, outputPath: string): Promise<void> {
      logger.debug('Creating ZIP', { sourceDir, outputPath });
      await runExecFile('zip', ['-r', outputPath, '.'], { cwd: sourceDir });
    },
  };
}
