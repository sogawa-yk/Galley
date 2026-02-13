import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

export type LogLevel = 'debug' | 'info' | 'warning' | 'error';

export interface Logger {
  debug(message: string, data?: unknown): void;
  info(message: string, data?: unknown): void;
  warning(message: string, data?: unknown): void;
  error(message: string, data?: unknown): void;
  setServer(server: McpServer): void;
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

  return {
    debug: (message, data?) => log('debug', message, data),
    info: (message, data?) => log('info', message, data),
    warning: (message, data?) => log('warning', message, data),
    error: (message, data?) => log('error', message, data),
    setServer(server: McpServer) {
      mcpServer = server;
    },
  };
}
