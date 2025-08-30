/**
 * 日志记录器
 * 提供统一的日志记录接口
 */
export class Logger {
  private static instance: Logger;
  private logLevel: LogLevel = LogLevel.INFO;

  private constructor() {}

  static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  setLogLevel(level: LogLevel): void {
    this.logLevel = level;
  }

  debug(message: string, ...args: any[]): void {
    if (this.logLevel <= LogLevel.DEBUG) {
      console.debug(`[DEBUG] ${new Date().toISOString()} - ${message}`, ...args);
    }
  }

  info(message: string, ...args: any[]): void {
    if (this.logLevel <= LogLevel.INFO) {
      console.info(`[INFO] ${new Date().toISOString()} - ${message}`, ...args);
    }
  }

  warn(message: string, ...args: any[]): void {
    if (this.logLevel <= LogLevel.WARN) {
      console.warn(`[WARN] ${new Date().toISOString()} - ${message}`, ...args);
    }
  }

  error(message: string, error?: Error, ...args: any[]): void {
    if (this.logLevel <= LogLevel.ERROR) {
      console.error(`[ERROR] ${new Date().toISOString()} - ${message}`, error, ...args);
    }
  }
}

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3
}

// 导出默认实例
export const logger = Logger.getInstance();