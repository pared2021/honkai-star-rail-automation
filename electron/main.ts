import { app, BrowserWindow, ipcMain, Menu } from 'electron';
import * as path from 'path';
import { spawn, ChildProcess } from 'child_process';

class ElectronApp {
  private mainWindow: BrowserWindow | null = null;
  private apiServer: ChildProcess | null = null;
  private isDev = process.env.NODE_ENV === 'development';

  constructor() {
    this.initializeApp();
  }

  private initializeApp(): void {
    // 当 Electron 完成初始化并准备创建浏览器窗口时调用此方法
    app.whenReady().then(() => {
      this.createWindow();
      this.startApiServer();
      this.setupMenu();
    });

    // 当所有窗口都关闭时退出应用
    app.on('window-all-closed', () => {
      if (process.platform !== 'darwin') {
        this.cleanup();
        app.quit();
      }
    });

    // 在 macOS 上，当点击 dock 图标并且没有其他窗口打开时，重新创建窗口
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        this.createWindow();
      }
    });

    // 应用退出前清理资源
    app.on('before-quit', () => {
      this.cleanup();
    });
  }

  private createWindow(): void {
    // 创建浏览器窗口
    this.mainWindow = new BrowserWindow({
      width: 1200,
      height: 800,
      minWidth: 1000,
      minHeight: 600,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        enableRemoteModule: false,
        preload: path.join(__dirname, 'preload.js')
      },
      icon: path.join(__dirname, '../assets/icon.png'),
      title: '崩坏星穹铁道自动化程序',
      show: false // 先不显示，等加载完成后再显示
    });

    // 加载应用
    if (this.isDev) {
      this.mainWindow.loadURL('http://localhost:5173');
      this.mainWindow.webContents.openDevTools();
    } else {
      this.mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
    }

    // 当窗口准备好显示时显示窗口
    this.mainWindow.once('ready-to-show', () => {
      this.mainWindow?.show();
    });

    // 当窗口关闭时清理引用
    this.mainWindow.on('closed', () => {
      this.mainWindow = null;
    });

    // 设置IPC处理程序
    this.setupIpcHandlers();
  }

  private startApiServer(): void {
    try {
      // 启动API服务器
      const apiPath = path.join(__dirname, '../api/index.js');
      this.apiServer = spawn('node', [apiPath], {
        stdio: 'pipe',
        env: { ...process.env, NODE_ENV: this.isDev ? 'development' : 'production' }
      });

      this.apiServer.stdout?.on('data', (data) => {
        console.log(`API Server: ${data}`);
      });

      this.apiServer.stderr?.on('data', (data) => {
        console.error(`API Server Error: ${data}`);
      });

      this.apiServer.on('close', (code) => {
        console.log(`API Server exited with code ${code}`);
      });

      console.log('API服务器启动中...');
    } catch (error) {
      console.error('启动API服务器失败:', error);
    }
  }

  private setupMenu(): void {
    const template = [
      {
        label: '文件',
        submenu: [
          {
            label: '退出',
            accelerator: 'CmdOrCtrl+Q',
            click: () => {
              app.quit();
            }
          }
        ]
      },
      {
        label: '编辑',
        submenu: [
          { label: '撤销', accelerator: 'CmdOrCtrl+Z', role: 'undo' },
          { label: '重做', accelerator: 'Shift+CmdOrCtrl+Z', role: 'redo' },
          { type: 'separator' },
          { label: '剪切', accelerator: 'CmdOrCtrl+X', role: 'cut' },
          { label: '复制', accelerator: 'CmdOrCtrl+C', role: 'copy' },
          { label: '粘贴', accelerator: 'CmdOrCtrl+V', role: 'paste' }
        ]
      },
      {
        label: '视图',
        submenu: [
          { label: '重新加载', accelerator: 'CmdOrCtrl+R', role: 'reload' },
          { label: '强制重新加载', accelerator: 'CmdOrCtrl+Shift+R', role: 'forceReload' },
          { label: '开发者工具', accelerator: 'F12', role: 'toggleDevTools' },
          { type: 'separator' },
          { label: '实际大小', accelerator: 'CmdOrCtrl+0', role: 'resetZoom' },
          { label: '放大', accelerator: 'CmdOrCtrl+Plus', role: 'zoomIn' },
          { label: '缩小', accelerator: 'CmdOrCtrl+-', role: 'zoomOut' },
          { type: 'separator' },
          { label: '全屏', accelerator: 'F11', role: 'togglefullscreen' }
        ]
      },
      {
        label: '帮助',
        submenu: [
          {
            label: '关于',
            click: () => {
              // 显示关于对话框
            }
          }
        ]
      }
    ];

    const menu = Menu.buildFromTemplate(template as any);
    Menu.setApplicationMenu(menu);
  }

  private setupIpcHandlers(): void {
    // 获取应用版本
    ipcMain.handle('get-app-version', () => {
      return app.getVersion();
    });

    // 最小化窗口
    ipcMain.handle('minimize-window', () => {
      this.mainWindow?.minimize();
    });

    // 最大化/还原窗口
    ipcMain.handle('toggle-maximize-window', () => {
      if (this.mainWindow?.isMaximized()) {
        this.mainWindow.unmaximize();
      } else {
        this.mainWindow?.maximize();
      }
    });

    // 关闭窗口
    ipcMain.handle('close-window', () => {
      this.mainWindow?.close();
    });

    // 重启应用
    ipcMain.handle('restart-app', () => {
      app.relaunch();
      app.exit();
    });
  }

  private cleanup(): void {
    // 停止API服务器
    if (this.apiServer) {
      this.apiServer.kill();
      this.apiServer = null;
    }
  }
}

// 创建应用实例
new ElectronApp();