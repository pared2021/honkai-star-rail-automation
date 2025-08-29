// Jest setup file
// Global test configuration and mocks

// Mock node-window-manager
jest.mock('node-window-manager', () => ({
  windowManager: {
    getWindows: jest.fn(() => []),
    getActiveWindow: jest.fn(() => null)
  }
}));

// Mock active-win
jest.mock('active-win', () => ({
  default: jest.fn(() => Promise.resolve(null))
}));

// Mock ps-list
jest.mock('ps-list', () => ({
  default: jest.fn(() => Promise.resolve([]))
}));

// Global test timeout
jest.setTimeout(10000);