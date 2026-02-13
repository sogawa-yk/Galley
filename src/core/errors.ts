import type { Logger } from './logger.js';

export type GalleyErrorCode =
  | 'SESSION_NOT_FOUND'
  | 'INVALID_SESSION_STATUS'
  | 'VALIDATION_ERROR'
  | 'FILE_READ_ERROR'
  | 'FILE_WRITE_ERROR'
  | 'INVALID_FILENAME'
  | 'PATH_TRAVERSAL'
  | 'CONFIG_LOAD_ERROR';

export class GalleyError extends Error {
  constructor(
    public readonly code: GalleyErrorCode,
    message: string,
    public readonly cause?: unknown,
  ) {
    super(message);
    this.name = 'GalleyError';
  }
}

export function wrapToolHandler(
  handler: (args: Record<string, unknown>) => Promise<{ content: Array<{ type: 'text'; text: string }> }>,
  logger: Logger,
) {
  return async (args: Record<string, unknown>) => {
    try {
      return await handler(args);
    } catch (error) {
      if (error instanceof GalleyError) {
        return {
          content: [{ type: 'text' as const, text: `Error [${error.code}]: ${error.message}` }],
          isError: true,
        };
      }
      logger.error('Unexpected error', error);
      return {
        content: [{ type: 'text' as const, text: 'Internal server error' }],
        isError: true,
      };
    }
  };
}
