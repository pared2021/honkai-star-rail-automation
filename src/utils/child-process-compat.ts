// child_process 浏览器兼容性模块

// 模拟 exec 函数
const exec = () => { console.debug('child-process-compat exec called'); };

// 模拟 child_process 模块
const mockChildProcess = {
  exec
};

// 提供默认导出和命名导出
export default mockChildProcess;
export { exec };