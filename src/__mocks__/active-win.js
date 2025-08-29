// Mock for active-win module
module.exports = async function activeWin() {
  return {
    title: '崩坏：星穹铁道',
    id: 12345,
    bounds: {
      x: 0,
      y: 0,
      width: 1920,
      height: 1080
    },
    owner: {
      name: 'StarRail.exe',
      processId: 1234,
      bundleId: 'com.mihoyo.starrail'
    },
    memoryUsage: 512000000
  };
};