// crypto 浏览器兼容性模块

// 模拟 createHash 函数
const createHash = (_algorithm: string) => {
  console.debug('createHash called with algorithm:', _algorithm);
  return {
    update: (data: any) => ({
      digest: (_encoding?: string) => {
        console.debug('digest called with encoding:', _encoding);
        // 在浏览器环境中返回一个简单的哈希值
        if (typeof data === 'string') {
          let hash = 0;
          for (let i = 0; i < data.length; i++) {
            const char = data.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
          }
          return Math.abs(hash).toString(16);
        }
        return 'mock-hash';
      }
    })
  };
};

// 模拟 crypto 模块
const mockCrypto = {
  createHash
};

// 提供默认导出和命名导出
export default mockCrypto;
export { createHash };