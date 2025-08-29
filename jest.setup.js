// Jest setup file

// Mock node-window-manager
jest.mock('node-window-manager', () => ({
  windowManager: {
    getWindows: jest.fn(() => [
      {
        getTitle: () => '崩坏：星穹铁道',
        getBounds: () => ({ x: 0, y: 0, width: 1920, height: 1080 })
      }
    ])
  }
}));

// Set test environment
process.env.NODE_ENV = 'test';