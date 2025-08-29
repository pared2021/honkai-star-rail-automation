import InputController from '../InputController';
import * as robot from 'robotjs';

// Mock robotjs
jest.mock('robotjs', () => ({
  moveMouse: jest.fn(),
  mouseClick: jest.fn(),
  mouseToggle: jest.fn(),
  keyTap: jest.fn(),
  keyToggle: jest.fn(),
  typeString: jest.fn(),
  dragMouse: jest.fn(),
  scrollMouse: jest.fn(),
  getMousePos: jest.fn(() => ({ x: 100, y: 200 })),
  setMouseDelay: jest.fn(),
  setKeyboardDelay: jest.fn()
}));

const mockRobot = robot as jest.Mocked<typeof robot>;

describe('InputController', () => {
  let inputController: InputController;

  beforeEach(() => {
    inputController = new InputController();
    jest.clearAllMocks();
  });

  describe('基本功能测试', () => {
    test('应该能够启用和禁用输入控制', () => {
      expect(inputController.isInputEnabled()).toBe(true);
      
      inputController.setEnabled(false);
      expect(inputController.isInputEnabled()).toBe(false);
      
      inputController.setEnabled(true);
      expect(inputController.isInputEnabled()).toBe(true);
    });

    test('应该能够设置和获取默认延迟', () => {
      const newDelay = 200;
      inputController.setDefaultDelay(newDelay);
      expect(inputController.getDefaultDelay()).toBe(newDelay);
    });

    test('应该能够设置游戏窗口信息', () => {
      const gameWindow = { x: 100, y: 50, width: 800, height: 600 };
      inputController.setGameWindow(gameWindow);
      expect(inputController.getGameWindow()).toEqual(gameWindow);
    });
  });

  describe('鼠标操作测试', () => {
    beforeEach(() => {
      inputController.setEnabled(true);
    });

    test('应该能够执行鼠标点击', async () => {
      await inputController.click(100, 200);
      
      expect(mockRobot.moveMouse).toHaveBeenCalledWith(100, 200);
      expect(mockRobot.mouseClick).toHaveBeenCalledWith('left', false);
    });

    test('应该能够执行右键点击', async () => {
      await inputController.click(100, 200, { button: 'right' });
      
      expect(mockRobot.mouseClick).toHaveBeenCalledWith('right', false);
    });

    test('应该能够执行双击', async () => {
      await inputController.click(100, 200, { double: true });
      
      expect(mockRobot.mouseClick).toHaveBeenCalledWith('left', true);
    });

    test('应该能够移动鼠标', async () => {
      await inputController.moveMouse(300, 400);
      
      expect(mockRobot.moveMouse).toHaveBeenCalledWith(300, 400);
    });

    test('应该能够执行鼠标拖拽', async () => {
      await inputController.drag(100, 200, 300, 400);
      
      expect(mockRobot.moveMouse).toHaveBeenCalledWith(100, 200);
      expect(mockRobot.mouseToggle).toHaveBeenCalledWith('down');
      expect(mockRobot.moveMouse).toHaveBeenCalledWith(300, 400);
      expect(mockRobot.mouseToggle).toHaveBeenCalledWith('up');
    });

    test('应该能够执行滚轮操作', async () => {
      await inputController.scroll(100, 200, 'up', 3);
      
      expect(mockRobot.moveMouse).toHaveBeenCalledWith(100, 200);
      expect(mockRobot.scrollMouse).toHaveBeenCalledWith(3, 0);
    });

    test('应该能够获取当前鼠标位置', () => {
      const position = inputController.getCurrentMousePosition();
      
      expect(mockRobot.getMousePos).toHaveBeenCalled();
      expect(position).toEqual({ x: 100, y: 200 });
    });
  });

  describe('键盘操作测试', () => {
    beforeEach(() => {
      inputController.setEnabled(true);
    });

    test('应该能够按下单个按键', async () => {
      await inputController.pressKey('a');
      
      expect(mockRobot.keyTap).toHaveBeenCalledWith('a');
    });

    test('应该能够按下组合键', async () => {
      await inputController.pressKey('c', { modifiers: ['control'] });
      
      expect(mockRobot.keyTap).toHaveBeenCalledWith('c', ['control']);
    });

    test('应该能够输入文本', async () => {
      const text = 'Hello World';
      await inputController.typeText(text);
      
      expect(mockRobot.typeString).toHaveBeenCalledWith(text);
    });

    test('应该拒绝无效的按键', async () => {
      await expect(inputController.pressKey('invalid_key')).rejects.toThrow('无效的按键');
    });

    test('应该拒绝过长的文本', async () => {
      const longText = 'a'.repeat(1001);
      await expect(inputController.typeText(longText)).rejects.toThrow('文本长度超过限制');
    });
  });

  describe('安全检查测试', () => {
    beforeEach(() => {
      inputController.setEnabled(true);
      inputController.setSafetyChecks(true);
    });

    test('应该在输入控制禁用时拒绝操作', async () => {
      inputController.setEnabled(false);
      
      // 当输入控制禁用时，操作不会抛出错误，而是静默返回
      await inputController.click(100, 200);
      
      // 验证robotjs没有被调用
      expect(mockRobot.mouseClick).not.toHaveBeenCalled();
    });

    test('应该检查操作间隔', async () => {
      inputController.setEnabled(true);
      inputController.setSafetyChecks(true); // 启用安全检查
      
      // 设置更长的最小间隔用于测试
      (inputController as any).minActionInterval = 200;
      
      // 第一次点击
      await inputController.click(100, 200);
      expect(mockRobot.mouseClick).toHaveBeenCalledTimes(1);
      
      // 立即进行第二次点击（间隔太短）
      await inputController.click(100, 200);
      
      // 第二次点击应该被忽略（间隔太短）
      expect(mockRobot.mouseClick).toHaveBeenCalledTimes(1);
      
      // 等待足够的时间后再次点击
      await new Promise(resolve => setTimeout(resolve, 250));
      await inputController.click(100, 200);
      
      // 现在应该允许第三次点击
      expect(mockRobot.mouseClick).toHaveBeenCalledTimes(2);
    });
  });

  describe('坐标转换测试', () => {
    beforeEach(() => {
      inputController.setEnabled(true);
      inputController.setGameWindow({ x: 100, y: 50, width: 800, height: 600 });
    });

    test('应该能够获取游戏内鼠标位置', () => {
      const gamePosition = inputController.getCurrentMousePositionInGame();
      
      // 屏幕坐标 (100, 200) - 游戏窗口偏移 (100, 50) = 游戏坐标 (0, 150)
      expect(gamePosition).toEqual({ x: 0, y: 150 });
    });
  });

  describe('日志记录测试', () => {
    beforeEach(() => {
      inputController.setEnabled(true);
      inputController.clearLogs();
    });

    test('应该记录操作日志', async () => {
      await inputController.click(100, 200);
      
      const logs = inputController.getInputLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].action).toBe('click');
      expect(logs[0].coordinates).toEqual({ x: 100, y: 200 });
      expect(logs[0].success).toBe(true);
    });

    test('应该能够获取统计信息', async () => {
      await inputController.click(100, 200);
      await inputController.pressKey('a');
      
      const stats = inputController.getStats();
      expect(stats.total).toBe(2);
      expect(stats.success).toBe(2);
      expect(stats.failed).toBe(0);
      expect(stats.successRate).toBe(100);
    });

    test('应该能够清空日志', async () => {
      await inputController.click(100, 200);
      expect(inputController.getInputLogs()).toHaveLength(1);
      
      inputController.clearLogs();
      expect(inputController.getInputLogs()).toHaveLength(0);
    });

    test('应该限制日志数量', async () => {
      // 设置较小的日志限制进行测试
      const originalMaxLogs = (inputController as any).maxLogEntries;
      (inputController as any).maxLogEntries = 5;
      
      // 执行6次操作
      for (let i = 0; i < 6; i++) {
        await inputController.click(i, i);
      }
      
      const logs = inputController.getInputLogs();
      expect(logs.length).toBe(5); // 应该只保留最新的5条
      
      // 恢复原始设置
      (inputController as any).maxLogEntries = originalMaxLogs;
    });
  });

  describe('错误处理测试', () => {
    beforeEach(() => {
      inputController.setEnabled(true);
    });

    test('应该处理robotjs错误', async () => {
      mockRobot.mouseClick.mockImplementation(() => {
        throw new Error('Robot error');
      });
      
      // InputController会重新抛出错误
      await expect(inputController.click(100, 200)).rejects.toThrow('Robot error');
      
      const logs = inputController.getInputLogs();
      expect(logs[0].success).toBe(false);
    });

    test('应该处理获取鼠标位置错误', () => {
      mockRobot.getMousePos.mockImplementation(() => {
        throw new Error('Get position error');
      });
      
      const position = inputController.getCurrentMousePosition();
      expect(position).toEqual({ x: 0, y: 0 });
    });
  });
});