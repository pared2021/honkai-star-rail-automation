// util 浏览器兼容性模块
// 模拟 promisify 函数
const promisify = (fn) => fn;
// 模拟 util 模块
const mockUtil = {
    promisify
};
// 提供默认导出和命名导出
export default mockUtil;
export { promisify };
