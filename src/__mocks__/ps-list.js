// Mock for ps-list module
module.exports = async function psList() {
  return [
    {
      pid: 1234,
      name: 'StarRail.exe',
      cmd: 'C:\\Games\\StarRail\\StarRail.exe'
    },
    {
      pid: 5678,
      name: 'chrome.exe',
      cmd: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
    }
  ];
};

// Export as default for ES modules
module.exports.default = module.exports;