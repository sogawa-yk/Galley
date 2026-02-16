import { describe, it, expect, vi } from 'vitest';
import { GalleyError, wrapToolHandler } from '../../src/core/errors.js';
import type { Logger } from '../../src/core/logger.js';

function createMockLogger(): Logger {
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

describe('GalleyError', () => {
  it('should create an error with code and message', () => {
    const error = new GalleyError('SESSION_NOT_FOUND', 'Session not found');
    expect(error.code).toBe('SESSION_NOT_FOUND');
    expect(error.message).toBe('Session not found');
    expect(error.name).toBe('GalleyError');
  });

  it('should create an error with cause', () => {
    const cause = new Error('original');
    const error = new GalleyError('FILE_READ_ERROR', 'Read failed', cause);
    expect(error.cause).toBe(cause);
  });

  it('should be an instance of Error', () => {
    const error = new GalleyError('VALIDATION_ERROR', 'Invalid data');
    expect(error).toBeInstanceOf(Error);
    expect(error).toBeInstanceOf(GalleyError);
  });
});

describe('wrapToolHandler', () => {
  it('should return handler result on success', async () => {
    const logger = createMockLogger();
    const result = { content: [{ type: 'text', text: 'ok' }] };
    const handler = vi.fn().mockResolvedValue(result);

    const wrapped = wrapToolHandler(handler, logger);
    const actual = await wrapped({ foo: 'bar' });

    expect(actual).toEqual(result);
    expect(handler).toHaveBeenCalledWith({ foo: 'bar' });
  });

  it('should convert GalleyError to isError response', async () => {
    const logger = createMockLogger();
    const handler = vi.fn().mockRejectedValue(
      new GalleyError('SESSION_NOT_FOUND', 'Session abc not found'),
    );

    const wrapped = wrapToolHandler(handler, logger);
    const actual = await wrapped({});

    expect(actual).toEqual({
      content: [{ type: 'text', text: 'Error [SESSION_NOT_FOUND]: Session abc not found' }],
      isError: true,
    });
    expect(logger.error).not.toHaveBeenCalled();
  });

  it('should convert unexpected error to Internal server error', async () => {
    const logger = createMockLogger();
    const unexpectedError = new Error('something broke');
    const handler = vi.fn().mockRejectedValue(unexpectedError);

    const wrapped = wrapToolHandler(handler, logger);
    const actual = await wrapped({});

    expect(actual).toEqual({
      content: [{ type: 'text', text: 'Internal server error' }],
      isError: true,
    });
    expect(logger.error).toHaveBeenCalledWith('Unexpected error', unexpectedError);
  });
});
