// fs 浏览器兼容性模块

// 模拟 fs 模块的函数
const existsSync = (_path: string): boolean => {
  // 在浏览器环境中，总是返回false
  return false;
};

const readFileSync = (_path: string, _encoding?: string): string | Buffer => {
  throw new Error('fs.readFileSync is not available in browser environment');
};

const writeFileSync = (_path: string, _data: any, _encoding?: string): void => {
  throw new Error('fs.writeFileSync is not available in browser environment');
};

const mkdirSync = (_path: string, _options?: any): void => {
  throw new Error('fs.mkdirSync is not available in browser environment');
};

// 模拟 fs 模块
const mockFs = {
  existsSync,
  readFileSync,
  writeFileSync,
  mkdirSync
};

// 提供默认导出和命名导出
export default mockFs;
export { existsSync, readFileSync, writeFileSync, mkdirSync };