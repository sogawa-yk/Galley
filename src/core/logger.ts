import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Storage } from './storage.js';

export type LogLevel = 'debug' | 'info' | 'warning' | 'error';

export interface Logger {
  debug(message: string, data?: unknown): void;
  info(message: string, data?: unknown): void;
  warning(message: string, data?: unknown): void;
  error(message: string, data?: unknown): void;
  setServer(server: McpServer): void;
  forSession(sessionId: string, storage: Storage, toolName: string): Logger;
}

const LOG_LEVEL_PRIORITY: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warning: 2,
  error: 3,
};

export function createLogger(options: { level: LogLevel }): Logger {
  const minPriority = LOG_LEVEL_PRIORITY[options.level];
  let mcpServer: McpServer | undefined;

  function shouldLog(level: LogLevel): boolean {
    return LOG_LEVEL_PRIORITY[level] >= minPriority;
  }

  function log(level: LogLevel, message: string, data?: unknown): void {
    if (!shouldLog(level)) return;

    const formatted = data !== undefined ? `[${level}] ${message} ${JSON.stringify(data)}` : `[${level}] ${message}`;
    console.error(formatted);

    if (mcpServer) {
      mcpServer.sendLoggingMessage({ level, data: data !== undefined ? `${message} ${JSON.stringify(data)}` : message }).catch(() => {
        // Ignore errors from sendLoggingMessage
      });
    }
  }

  const logger: Logger = {
    debug: (message, data?) => log('debug', message, data),
    info: (message, data?) => log('info', message, data),
    warning: (message, data?) => log('warning', message, data),
    error: (message, data?) => log('error', message, data),
    setServer(server: McpServer) {
      mcpServer = server;
    },
    forSession(sessionId: string, storage: Storage, toolName: string): Logger {
      const logPath = `sessions/${sessionId}/galley.log`;

      function writeEntry(level: LogLevel, message: string, data?: unknown): void {
        const entry = JSON.stringify({
          timestamp: new Date().toISOString(),
          level,
          tool: toolName,
          message,
          ...(data !== undefined ? { data } : {}),
        });
        storage.appendText(logPath, entry + '\n').catch(() => {
          // Silently ignore file write errors — logging must not break tool execution
        });
      }

      return {
        debug(message: string, data?: unknown): void {
          logger.debug(message, data);
          if (shouldLog('debug')) writeEntry('debug', message, data);
        },
        info(message: string, data?: unknown): void {
          logger.info(message, data);
          if (shouldLog('info')) writeEntry('info', message, data);
        },
        warning(message: string, data?: unknown): void {
          logger.warning(message, data);
          if (shouldLog('warning')) writeEntry('warning', message, data);
        },
        error(message: string, data?: unknown): void {
          logger.error(message, data);
          if (shouldLog('error')) writeEntry('error', message, data);
        },
        setServer: (server) => logger.setServer(server),
        forSession: (sid, st, tn) => logger.forSession(sid, st, tn),
      };
    },
  };

  return logger;
}
