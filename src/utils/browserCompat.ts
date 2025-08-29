// 浏览器兼容性工具
// 检测运行环境
export const isBrowser = typeof window !== 'undefined';
export const isNode = !isBrowser;

// active-win 模拟
const mockActiveWin = () => Promise.resolve(null);
export default mockActiveWin;
export { mockActiveWin };

// ps-list 模拟
export const mockPsList = () => Promise.resolve([]);

// robotjs 模拟
export const mockRobotjs = {
  moveMouse: () => { console.debug('mockRobotjs.moveMouse called'); },
  mouseClick: () => { console.debug('mockRobotjs.mouseClick called'); },
  keyTap: () => { console.debug('mockRobotjs.keyTap called'); },
  dragMouse: () => { console.debug('mockRobotjs.dragMouse called'); },
  setMouseDelay: () => { console.debug('mockRobotjs.setMouseDelay called'); },
  setKeyboardDelay: () => { console.debug('mockRobotjs.setKeyboardDelay called'); }
};

// screenshot-desktop 模拟
export const mockScreenshot = () => Promise.resolve(Buffer.alloc(0));

// node-window-manager 模拟
export const mockWindowManager = {
  windowManager: {
    getWindows: () => []
  }
};

// child_process 模拟
export const mockChildProcess = {
  exec: () => { console.debug('mockChildProcess.exec called'); }
};

// util 模拟
export const mockUtil = {
  promisify: <T extends (...args: unknown[]) => unknown>(fn: T) => fn
};

// 模块映射
const mockModules = {
  'active-win': mockActiveWin,
  'ps-list': mockPsList,
  'robotjs': mockRobotjs,
  'screenshot-desktop': mockScreenshot,
  'node-window-manager': mockWindowManager,
  'child_process': mockChildProcess,
  'util': mockUtil
};

// 安全的模块加载器
export function safeRequire(moduleName: string) {
  if (isBrowser) {
    return mockModules[moduleName as keyof typeof mockModules] || null;
  }
  
  try {
    return require(moduleName);
  } catch (error) {
    console.warn(`Failed to load module ${moduleName}:`, error);
    return mockModules[moduleName as keyof typeof mockModules] || null;
  }
}