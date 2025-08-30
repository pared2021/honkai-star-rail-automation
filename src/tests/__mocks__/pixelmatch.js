// Mock for pixelmatch module
module.exports = function pixelmatch(img1, img2, output, width, height, options = {}) {
  // Mock implementation that returns a difference count
  // For testing purposes, return 0 (no differences) or a small number
  return 0;
};

// Export as default for ES modules
module.exports.default = module.exports;