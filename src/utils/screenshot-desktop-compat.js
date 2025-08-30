// screenshot-desktop 浏览器兼容性模块
// 模拟 screenshot-desktop 功能
const mockScreenshot = () => Promise.resolve(Buffer.alloc(0));
// 提供默认导出
export default mockScreenshot;
export { mockScreenshot };
