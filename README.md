# 星铁自动化助手

基于 React + TypeScript + Vite 构建的游戏自动化工具，专为《崩坏：星穹铁道》设计。

## 主要功能

- 🎮 游戏窗口检测和控制
- 🖼️ 图像识别和模板匹配
- 📋 任务信息收集和管理
- 🤖 自动化策略执行
- 📊 数据库存储和查询
- 🖥️ Electron 桌面应用支持

## 技术栈

- **前端**: React 18 + TypeScript + Vite + Tailwind CSS
- **后端**: Express.js + TypeScript
- **桌面**: Electron
- **数据库**: SQLite
- **测试**: Jest + Testing Library
- **图像处理**: Jimp + screenshot-desktop
- **自动化**: RobotJS + node-window-manager

## 项目结构

```
├── src/                    # 前端源码
│   ├── components/         # React 组件
│   ├── modules/           # 核心功能模块
│   ├── services/          # 服务层
│   ├── types/             # TypeScript 类型定义
│   └── utils/             # 工具函数
├── api/                   # 后端 API
├── electron/              # Electron 主进程
├── templates/             # 图像识别模板
├── database/              # 数据库相关
└── tests/                 # 测试文件
```

## 快速开始

### 安装依赖
```bash
npm install
```

### 开发模式
```bash
# 启动前端开发服务器
npm run dev

# 启动后端 API 服务器
npm run api:dev

# 启动 Electron 应用
npm run electron:dev
```

### 构建
```bash
# 构建前端
npm run build

# 构建 API
npm run api:build

# 构建 Electron 应用
npm run electron:build
```

### 测试
```bash
# 运行测试
npm test

# 运行测试覆盖率
npm run test:coverage
```

## 核心模块

- **GameDetector**: 游戏窗口检测和管理
- **ImageRecognition**: 图像识别和模板匹配
- **TaskInfoCollector**: 任务信息收集
- **InputController**: 输入控制和自动化
- **DatabaseService**: 数据库操作
- **StrategyExecutor**: 策略执行引擎

## 注意事项

- 需要管理员权限运行（用于窗口控制和输入模拟）
- 支持 Windows 系统
- 确保游戏运行在前台
- 建议使用 1920x1080 分辨率以获得最佳识别效果
