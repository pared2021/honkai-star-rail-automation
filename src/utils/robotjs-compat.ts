// robotjs 浏览器兼容性模块

// 模拟 robotjs 功能
const mockRobotjs = {
  moveMouse: () => {
    // 浏览器环境中不支持鼠标控制
  },
  mouseClick: () => {
    // 浏览器环境中不支持鼠标点击
  },
  keyTap: () => {
    // 浏览器环境中不支持键盘模拟
  },
  dragMouse: () => {
    // 浏览器环境中不支持鼠标拖拽
  },
  setMouseDelay: () => {
    // 浏览器环境中不支持鼠标延迟设置
  },
  setKeyboardDelay: () => {
    // 浏览器环境中不支持键盘延迟设置
  }
};

// 提供默认导出
export default mockRobotjs;