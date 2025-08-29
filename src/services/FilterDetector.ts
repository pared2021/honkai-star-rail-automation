import { exec } from 'child_process';
import { promisify } from 'util';
import { ThirdPartyToolInfo } from '../types/index.js';

const execAsync = promisify(exec);

/**
 * 游戏滤镜和第三方工具检测器
 * 专门用于检测可能影响游戏画面或性能的第三方工具
 */
export class FilterDetector {
  private knownFilterTools = [
    // 游戏加加
    {
      name: '游戏加加',
      type: 'game_enhancer',
      processNames: ['GamePP.exe', 'GamePPService.exe'],
      windowTitles: ['游戏加加', 'GamePP'],
      registryKeys: [
        'HKEY_LOCAL_MACHINE\\SOFTWARE\\GamePP',
        'HKEY_CURRENT_USER\\SOFTWARE\\GamePP'
      ],
      description: '游戏性能优化和画面增强工具',
      riskLevel: 'medium' as const
    },
    // MSI Afterburner
    {
      name: 'MSI Afterburner',
      type: 'gpu_tool',
      processNames: ['MSIAfterburner.exe', 'RTSS.exe'],
      windowTitles: ['MSI Afterburner', 'RivaTuner Statistics Server'],
      registryKeys: [
        'HKEY_LOCAL_MACHINE\\SOFTWARE\\MSI\\Afterburner',
        'HKEY_CURRENT_USER\\SOFTWARE\\MSI\\Afterburner'
      ],
      description: '显卡超频和监控工具',
      riskLevel: 'low' as const
    },
    // NVIDIA GeForce Experience
    {
      name: 'NVIDIA GeForce Experience',
      type: 'gpu_tool',
      processNames: ['NvContainer.exe', 'nvsphelper64.exe', 'NVIDIA Web Helper.exe'],
      windowTitles: ['NVIDIA GeForce Experience'],
      registryKeys: [
        'HKEY_LOCAL_MACHINE\\SOFTWARE\\NVIDIA Corporation\\Global\\GeForceExperience'
      ],
      description: 'NVIDIA 游戏优化和录制工具',
      riskLevel: 'low' as const
    },
    // AMD Radeon Software
    {
      name: 'AMD Radeon Software',
      type: 'gpu_tool',
      processNames: ['RadeonSoftware.exe', 'AMDRSServ.exe'],
      windowTitles: ['AMD Radeon Software'],
      registryKeys: [
        'HKEY_LOCAL_MACHINE\\SOFTWARE\\AMD\\CN'
      ],
      description: 'AMD 显卡驱动和优化软件',
      riskLevel: 'low' as const
    },
    // ReShade
    {
      name: 'ReShade',
      type: 'graphics_filter',
      processNames: ['ReShade.exe'],
      windowTitles: ['ReShade'],
      registryKeys: [
        'HKEY_LOCAL_MACHINE\\SOFTWARE\\ReShade'
      ],
      description: '游戏画面后处理和滤镜工具',
      riskLevel: 'high' as const
    },
    // Bandicam
    {
      name: 'Bandicam',
      type: 'recording_tool',
      processNames: ['bdcam.exe', 'bandicam.exe'],
      windowTitles: ['Bandicam'],
      registryKeys: [
        'HKEY_LOCAL_MACHINE\\SOFTWARE\\Bandicam Company\\BANDICAM'
      ],
      description: '屏幕录制软件',
      riskLevel: 'medium' as const
    },
    // OBS Studio
    {
      name: 'OBS Studio',
      type: 'recording_tool',
      processNames: ['obs64.exe', 'obs32.exe'],
      windowTitles: ['OBS Studio'],
      registryKeys: [],
      description: '开源直播和录制软件',
      riskLevel: 'low' as const
    },
    // Fraps
    {
      name: 'Fraps',
      type: 'recording_tool',
      processNames: ['fraps.exe'],
      windowTitles: ['Fraps'],
      registryKeys: [
        'HKEY_LOCAL_MACHINE\\SOFTWARE\\Fraps'
      ],
      description: '游戏帧率显示和录制工具',
      riskLevel: 'medium' as const
    }
  ];

  /**
   * 检测所有已知的滤镜和第三方工具
   */
  public async detectAllFilterTools(): Promise<ThirdPartyToolInfo[]> {
    const detectedTools: ThirdPartyToolInfo[] = [];

    for (const tool of this.knownFilterTools) {
      const detection = await this.detectSpecificTool(tool);
      if (detection.isDetected) {
        detectedTools.push({
          name: tool.name,
          type: (tool.type as 'overlay' | 'recorder' | 'injection' | 'filter' | 'game_enhancer' | 'gpu_tool' | 'graphics_filter' | 'recording_tool' | 'unknown') || 'unknown',
          isDetected: true,
          processName: detection.detectedProcesses.join(', '),
          windowTitle: detection.detectedWindows.join(', '),
          description: tool.description,
          riskLevel: tool.riskLevel,
          detectionMethods: detection.detectionMethods
        });
      }
    }

    return detectedTools;
  }

  /**
   * 检测特定工具
   */
  private async detectSpecificTool(tool: any): Promise<{
    isDetected: boolean;
    detectedProcesses: string[];
    detectedWindows: string[];
    detectionMethods: string[];
  }> {
    const detectedProcesses: string[] = [];
    const detectedWindows: string[] = [];
    const detectionMethods: string[] = [];

    // 检测进程
    for (const processName of tool.processNames) {
      const isRunning = await this.isProcessRunning(processName);
      if (isRunning) {
        detectedProcesses.push(processName);
        detectionMethods.push('process');
      }
    }

    // 检测窗口
    for (const windowTitle of tool.windowTitles) {
      const windowExists = await this.isWindowExists(windowTitle);
      if (windowExists) {
        detectedWindows.push(windowTitle);
        detectionMethods.push('window');
      }
    }

    // 检测注册表
    for (const registryKey of tool.registryKeys) {
      const keyExists = await this.isRegistryKeyExists(registryKey);
      if (keyExists) {
        detectionMethods.push('registry');
      }
    }

    return {
      isDetected: detectedProcesses.length > 0 || detectedWindows.length > 0 || detectionMethods.includes('registry'),
      detectedProcesses,
      detectedWindows,
      detectionMethods: [...new Set(detectionMethods)]
    };
  }

  /**
   * 检测进程是否正在运行
   */
  private async isProcessRunning(processName: string): Promise<boolean> {
    try {
      const { stdout } = await execAsync(`tasklist /FI "IMAGENAME eq ${processName}" /FO CSV`);
      return stdout.includes(processName);
    } catch (error) {
      console.error(`检测进程 ${processName} 失败:`, error);
      return false;
    }
  }

  /**
   * 检测窗口是否存在
   */
  private async isWindowExists(windowTitle: string): Promise<boolean> {
    try {
      // 使用 PowerShell 检测窗口
      const command = `powershell "Get-Process | Where-Object {$_.MainWindowTitle -like '*${windowTitle}*'} | Select-Object -First 1"`;
      const { stdout } = await execAsync(command);
      return stdout.trim().length > 0 && !stdout.includes('ProcessName');
    } catch (error) {
      console.error(`检测窗口 ${windowTitle} 失败:`, error);
      return false;
    }
  }

  /**
   * 检测注册表项是否存在
   */
  private async isRegistryKeyExists(registryKey: string): Promise<boolean> {
    try {
      const command = `reg query "${registryKey}" 2>nul`;
      const { stdout } = await execAsync(command);
      return stdout.trim().length > 0;
    } catch (error) {
      // 注册表项不存在时会抛出错误，这是正常的
      return false;
    }
  }

  /**
   * 检测游戏是否被注入DLL
   */
  public async detectGameInjection(gameProcessId: number): Promise<{
    isInjected: boolean;
    suspiciousDlls: string[];
    injectionMethods: string[];
  }> {
    const suspiciousDlls: string[] = [];
    const injectionMethods: string[] = [];

    try {
      // 获取进程加载的所有DLL
      const command = `powershell "Get-Process -Id ${gameProcessId} | Select-Object -ExpandProperty Modules | Select-Object ModuleName, FileName"`;
      const { stdout } = await execAsync(command);
      
      const lines = stdout.split('\n').filter(line => line.trim());
      
      for (const line of lines) {
        const dllPath = line.trim();
        
        // 检测可疑的DLL
        if (this.isSuspiciousDll(dllPath)) {
          suspiciousDlls.push(dllPath);
          injectionMethods.push('dll_injection');
        }
      }

      return {
        isInjected: suspiciousDlls.length > 0,
        suspiciousDlls,
        injectionMethods: [...new Set(injectionMethods)]
      };

    } catch (error) {
      console.error('检测游戏注入失败:', error);
      return {
        isInjected: false,
        suspiciousDlls: [],
        injectionMethods: []
      };
    }
  }

  /**
   * 判断DLL是否可疑
   */
  private isSuspiciousDll(dllPath: string): boolean {
    const suspiciousPatterns = [
      /reshade/i,
      /gamepp/i,
      /overlay/i,
      /hook/i,
      /inject/i,
      /d3d.*hook/i,
      /opengl.*hook/i,
      /vulkan.*hook/i
    ];

    return suspiciousPatterns.some(pattern => pattern.test(dllPath));
  }

  /**
   * 检测显卡驱动级别的滤镜
   */
  public async detectDriverLevelFilters(): Promise<{
    hasDriverFilters: boolean;
    detectedFilters: string[];
  }> {
    const detectedFilters: string[] = [];

    try {
      // 检测 NVIDIA 滤镜
      const nvidiaFilters = await this.detectNvidiaFilters();
      detectedFilters.push(...nvidiaFilters);

      // 检测 AMD 滤镜
      const amdFilters = await this.detectAmdFilters();
      detectedFilters.push(...amdFilters);

      return {
        hasDriverFilters: detectedFilters.length > 0,
        detectedFilters
      };

    } catch (error) {
      console.error('检测驱动级滤镜失败:', error);
      return {
        hasDriverFilters: false,
        detectedFilters: []
      };
    }
  }

  /**
   * 检测 NVIDIA 滤镜
   */
  private async detectNvidiaFilters(): Promise<string[]> {
    const filters: string[] = [];

    try {
      // 检测 NVIDIA 控制面板设置
      const nvidiaKey = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\NVIDIA Corporation\\Global\\NVTweak';
      const keyExists = await this.isRegistryKeyExists(nvidiaKey);
      
      if (keyExists) {
        // 这里可以进一步检测具体的滤镜设置
        filters.push('NVIDIA 控制面板滤镜');
      }

      // 检测 GeForce Experience 滤镜
      const geforceKey = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\NVIDIA Corporation\\Global\\GeForceExperience\\ANSEL';
      const anselExists = await this.isRegistryKeyExists(geforceKey);
      
      if (anselExists) {
        filters.push('NVIDIA Ansel 滤镜');
      }

    } catch (error) {
      console.error('检测 NVIDIA 滤镜失败:', error);
    }

    return filters;
  }

  /**
   * 检测 AMD 滤镜
   */
  private async detectAmdFilters(): Promise<string[]> {
    const filters: string[] = [];

    try {
      // 检测 AMD Radeon 设置
      const amdKey = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\AMD\\CN';
      const keyExists = await this.isRegistryKeyExists(amdKey);
      
      if (keyExists) {
        filters.push('AMD Radeon 滤镜');
      }

    } catch (error) {
      console.error('检测 AMD 滤镜失败:', error);
    }

    return filters;
  }

  /**
   * 生成滤镜检测报告
   */
  public async generateFilterReport(): Promise<{
    summary: {
      totalToolsDetected: number;
      highRiskTools: number;
      mediumRiskTools: number;
      lowRiskTools: number;
    };
    detectedTools: ThirdPartyToolInfo[];
    driverFilters: string[];
    recommendations: string[];
  }> {
    const detectedTools = await this.detectAllFilterTools();
    const driverFilters = await this.detectDriverLevelFilters();
    
    const highRiskTools = detectedTools.filter(tool => tool.riskLevel === 'high').length;
    const mediumRiskTools = detectedTools.filter(tool => tool.riskLevel === 'medium').length;
    const lowRiskTools = detectedTools.filter(tool => tool.riskLevel === 'low').length;

    const recommendations: string[] = [];
    
    if (highRiskTools > 0) {
      recommendations.push('检测到高风险工具，建议关闭这些程序以确保游戏正常运行');
    }
    
    if (mediumRiskTools > 0) {
      recommendations.push('检测到中等风险工具，可能会影响游戏性能或画面');
    }
    
    if (driverFilters.detectedFilters.length > 0) {
      recommendations.push('检测到显卡驱动级滤镜，可能会影响游戏画面识别');
    }
    
    if (detectedTools.length === 0 && driverFilters.detectedFilters.length === 0) {
      recommendations.push('未检测到已知的第三方工具或滤镜，游戏环境良好');
    }

    return {
      summary: {
        totalToolsDetected: detectedTools.length,
        highRiskTools,
        mediumRiskTools,
        lowRiskTools
      },
      detectedTools,
      driverFilters: driverFilters.detectedFilters,
      recommendations
    };
  }

  /**
   * 实时监控滤镜状态变化
   */
  public startFilterMonitoring(callback: (report: any) => void, interval: number = 30000): NodeJS.Timeout {
    const monitor = async () => {
      try {
        const report = await this.generateFilterReport();
        callback(report);
      } catch (error) {
        console.error('滤镜监控失败:', error);
      }
    };

    // 立即执行一次
    monitor();
    
    // 设置定时监控
    return setInterval(monitor, interval);
  }

  /**
   * 停止滤镜监控
   */
  public stopFilterMonitoring(monitorId: NodeJS.Timeout): void {
    clearInterval(monitorId);
  }
}