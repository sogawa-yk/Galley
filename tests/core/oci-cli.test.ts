import { describe, it, expect, vi, beforeEach } from 'vitest';
import { GalleyError } from '../../src/core/errors.js';

// Mock child_process before importing the module
vi.mock('node:child_process', () => ({
  execFile: vi.fn(),
}));

import { execFile as execFileMock } from 'node:child_process';
import { createOciCli } from '../../src/core/oci-cli.js';
import type { Logger } from '../../src/core/logger.js';

function makeMockLogger(): Logger {
  const logger: Logger = {
    debug: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
    error: vi.fn(),
    setServer: vi.fn(),
    forSession: vi.fn(() => logger),
  };
  return logger;
}

// Helper to make execFile mock resolve
function mockExecFileSuccess(stdout: string, stderr = '') {
  const mock = execFileMock as unknown as ReturnType<typeof vi.fn>;
  mock.mockImplementation((_cmd: string, _args: string[], _opts: unknown, cb: (err: Error | null, result: { stdout: string; stderr: string }) => void) => {
    cb(null, { stdout, stderr });
  });
}

// Helper to make execFile mock reject with ENOENT
function mockExecFileNotFound() {
  const mock = execFileMock as unknown as ReturnType<typeof vi.fn>;
  mock.mockImplementation((_cmd: string, _args: string[], _opts: unknown, cb: (err: NodeJS.ErrnoException) => void) => {
    const err = new Error('spawn oci ENOENT') as NodeJS.ErrnoException;
    err.code = 'ENOENT';
    cb(err);
  });
}

// Helper to make execFile mock reject with an error
function mockExecFileError(message: string, stderr = '') {
  const mock = execFileMock as unknown as ReturnType<typeof vi.fn>;
  mock.mockImplementation((_cmd: string, _args: string[], _opts: unknown, cb: (err: NodeJS.ErrnoException & { stderr?: string }) => void) => {
    const err = new Error(message) as NodeJS.ErrnoException & { stderr?: string };
    err.code = 'ERR';
    err.stderr = stderr;
    cb(err);
  });
}

describe('OciCli', () => {
  let logger: Logger;

  beforeEach(() => {
    vi.clearAllMocks();
    logger = makeMockLogger();
  });

  describe('checkVersion', () => {
    it('should return oci version string', async () => {
      mockExecFileSuccess('3.41.0\n');
      const cli = createOciCli(logger);
      const version = await cli.checkVersion();
      expect(version).toBe('3.41.0');
    });

    it('should throw OCI_CLI_NOT_FOUND when oci is not installed', async () => {
      mockExecFileNotFound();
      const cli = createOciCli(logger);
      await expect(cli.checkVersion()).rejects.toThrow(GalleyError);
      await expect(cli.checkVersion()).rejects.toMatchObject({ code: 'OCI_CLI_NOT_FOUND' });
    });
  });

  describe('checkZip', () => {
    it('should return zip version string', async () => {
      mockExecFileSuccess('Copyright (c) Info-ZIP\nZip 3.0\n');
      const cli = createOciCli(logger);
      const version = await cli.checkZip();
      expect(version).toBe('Copyright (c) Info-ZIP');
    });

    it('should throw OCI_CLI_NOT_FOUND when zip is not installed', async () => {
      mockExecFileNotFound();
      const cli = createOciCli(logger);
      await expect(cli.checkZip()).rejects.toThrow(GalleyError);
      await expect(cli.checkZip()).rejects.toMatchObject({ code: 'OCI_CLI_NOT_FOUND' });
    });
  });

  describe('execute', () => {
    it('should build args correctly and parse JSON response', async () => {
      const jsonResponse = JSON.stringify({ data: { id: 'ocid1.stack.xxx' } });
      mockExecFileSuccess(jsonResponse);

      const cli = createOciCli(logger);
      const result = await cli.execute(
        ['resource-manager', 'stack', 'create'],
        { 'compartment-id': 'ocid1.compartment.xxx', 'display-name': 'test' },
      );

      expect(result.parsed).toEqual({ data: { id: 'ocid1.stack.xxx' } });
      expect(result.stdout).toBe(jsonResponse);

      // Verify execFile was called with correct args
      const mock = execFileMock as unknown as ReturnType<typeof vi.fn>;
      const callArgs = mock.mock.calls[0] as [string, string[]];
      expect(callArgs[0]).toBe('oci');
      expect(callArgs[1]).toContain('--output');
      expect(callArgs[1]).toContain('json');
      expect(callArgs[1]).toContain('resource-manager');
      expect(callArgs[1]).toContain('stack');
      expect(callArgs[1]).toContain('create');
      expect(callArgs[1]).toContain('--compartment-id');
      expect(callArgs[1]).toContain('ocid1.compartment.xxx');
    });

    it('should add --wait-for-state when specified', async () => {
      mockExecFileSuccess('{}');
      const cli = createOciCli(logger);
      await cli.execute(
        ['resource-manager', 'stack', 'create'],
        {},
        { waitForState: 'ACTIVE' },
      );

      const mock = execFileMock as unknown as ReturnType<typeof vi.fn>;
      const callArgs = mock.mock.calls[0] as [string, string[]];
      expect(callArgs[1]).toContain('--wait-for-state');
      expect(callArgs[1]).toContain('ACTIVE');
      expect(callArgs[1]).toContain('--wait-interval-seconds');
      expect(callArgs[1]).toContain('5');
    });

    it('should handle non-JSON output gracefully', async () => {
      mockExecFileSuccess('not json');
      const cli = createOciCli(logger);
      const result = await cli.execute(['resource-manager', 'stack', 'list'], {});
      expect(result.parsed).toBeNull();
      expect(result.stdout).toBe('not json');
    });

    it('should throw OCI_CLI_ERROR on command failure', async () => {
      mockExecFileError('command failed', 'ServiceError: 404');
      const cli = createOciCli(logger);
      await expect(
        cli.execute(['resource-manager', 'stack', 'get'], { 'stack-id': 'bad' }),
      ).rejects.toMatchObject({ code: 'OCI_CLI_ERROR' });
    });
  });

  describe('createZip', () => {
    it('should call zip with correct arguments', async () => {
      mockExecFileSuccess('');
      const cli = createOciCli(logger);
      await cli.createZip('/tmp/terraform', '/tmp/output.zip');

      const mock = execFileMock as unknown as ReturnType<typeof vi.fn>;
      const callArgs = mock.mock.calls[0] as [string, string[], { cwd?: string }];
      expect(callArgs[0]).toBe('zip');
      expect(callArgs[1]).toEqual(['-r', '/tmp/output.zip', '.']);
      expect(callArgs[2]).toMatchObject({ cwd: '/tmp/terraform' });
    });

    it('should throw OCI_CLI_NOT_FOUND when zip is not installed', async () => {
      mockExecFileNotFound();
      const cli = createOciCli(logger);
      await expect(cli.createZip('/tmp/src', '/tmp/out.zip')).rejects.toMatchObject({ code: 'OCI_CLI_NOT_FOUND' });
    });
  });
});
