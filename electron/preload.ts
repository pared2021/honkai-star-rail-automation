import { contextBridge, ipcRenderer } from 'electron';

// 定义暴露给渲染进程的API接口
interface ElectronAPI {
  // 应用控制
  getAppVersion: () => Promise<string>;
  minimizeWindow: () => Promise<void>;
  toggleMaximizeWindow: () => Promise<void>;
  closeWindow: () => Promise<void>;
  restartApp: () => Promise<void>;
  
  // 系统信息
  platform: string;
  
  // 事件监听
  onWindowStateChange: (callback: (state: 'maximized' | 'unmaximized') => void) => void;
  removeAllListeners: (channel: string) => void;
}

// 安全地暴露API到渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 应用控制
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
  toggleMaximizeWindow: () => ipcRenderer.invoke('toggle-maximize-window'),
  closeWindow: () => ipcRenderer.invoke('close-window'),
  restartApp: () => ipcRenderer.invoke('restart-app'),
  
  // 系统信息
  platform: process.platform,
  
  // 事件监听
  onWindowStateChange: (callback: (state: 'maximized' | 'unmaximized') => void) => {
    ipcRenderer.on('window-state-change', (_, state) => callback(state));
  },
  
  removeAllListeners: (channel: string) => {
    ipcRenderer.removeAllListeners(channel);
  }
} as ElectronAPI);

// 类型声明，供TypeScript使用
declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}