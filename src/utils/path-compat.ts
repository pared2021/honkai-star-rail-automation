// path 浏览器兼容性模块

// 模拟 path 模块的函数
const join = (...paths: string[]): string => {
  return paths.filter(p => p).join('/');
};

const resolve = (...paths: string[]): string => {
  return paths.filter(p => p).join('/');
};

const dirname = (path: string): string => {
  const parts = path.split('/');
  return parts.slice(0, -1).join('/') || '/';
};

const basename = (path: string, ext?: string): string => {
  const parts = path.split('/');
  let name = parts[parts.length - 1] || '';
  if (ext && name.endsWith(ext)) {
    name = name.slice(0, -ext.length);
  }
  return name;
};

const extname = (path: string): string => {
  const parts = path.split('.');
  return parts.length > 1 ? '.' + parts[parts.length - 1] : '';
};

const normalize = (path: string): string => {
  return path.replace(/\\/g, '/');
};

const isAbsolute = (path: string): boolean => {
  return path.startsWith('/') || /^[a-zA-Z]:/.test(path);
};

// 模拟 path 模块
const mockPath = {
  join,
  resolve,
  dirname,
  basename,
  extname,
  normalize,
  isAbsolute,
  sep: '/'
};

// 提供默认导出和命名导出
export default mockPath;
export { join, resolve, dirname, basename, extname, normalize, isAbsolute };