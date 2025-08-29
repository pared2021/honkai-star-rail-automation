import { exec } from 'child_process';
import { promisify } from 'util';
const execAsync = promisify(exec);
export class FilterDetector {
    constructor() {
        this.knownFilterTools = [
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
                riskLevel: 'medium'
            },
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
                riskLevel: 'low'
            },
            {
                name: 'NVIDIA GeForce Experience',
                type: 'gpu_tool',
                processNames: ['NvContainer.exe', 'nvsphelper64.exe', 'NVIDIA Web Helper.exe'],
                windowTitles: ['NVIDIA GeForce Experience'],
                registryKeys: [
                    'HKEY_LOCAL_MACHINE\\SOFTWARE\\NVIDIA Corporation\\Global\\GeForceExperience'
                ],
                description: 'NVIDIA 游戏优化和录制工具',
                riskLevel: 'low'
            },
            {
                name: 'AMD Radeon Software',
                type: 'gpu_tool',
                processNames: ['RadeonSoftware.exe', 'AMDRSServ.exe'],
                windowTitles: ['AMD Radeon Software'],
                registryKeys: [
                    'HKEY_LOCAL_MACHINE\\SOFTWARE\\AMD\\CN'
                ],
                description: 'AMD 显卡驱动和优化软件',
                riskLevel: 'low'
            },
            {
                name: 'ReShade',
                type: 'graphics_filter',
                processNames: ['ReShade.exe'],
                windowTitles: ['ReShade'],
                registryKeys: [
                    'HKEY_LOCAL_MACHINE\\SOFTWARE\\ReShade'
                ],
                description: '游戏画面后处理和滤镜工具',
                riskLevel: 'high'
            },
            {
                name: 'Bandicam',
                type: 'recording_tool',
                processNames: ['bdcam.exe', 'bandicam.exe'],
                windowTitles: ['Bandicam'],
                registryKeys: [
                    'HKEY_LOCAL_MACHINE\\SOFTWARE\\Bandicam Company\\BANDICAM'
                ],
                description: '屏幕录制软件',
                riskLevel: 'medium'
            },
            {
                name: 'OBS Studio',
                type: 'recording_tool',
                processNames: ['obs64.exe', 'obs32.exe'],
                windowTitles: ['OBS Studio'],
                registryKeys: [],
                description: '开源直播和录制软件',
                riskLevel: 'low'
            },
            {
                name: 'Fraps',
                type: 'recording_tool',
                processNames: ['fraps.exe'],
                windowTitles: ['Fraps'],
                registryKeys: [
                    'HKEY_LOCAL_MACHINE\\SOFTWARE\\Fraps'
                ],
                description: '游戏帧率显示和录制工具',
                riskLevel: 'medium'
            }
        ];
    }
    async detectAllFilterTools() {
        const detectedTools = [];
        for (const tool of this.knownFilterTools) {
            const detection = await this.detectSpecificTool(tool);
            if (detection.isDetected) {
                detectedTools.push({
                    name: tool.name,
                    type: tool.type || 'unknown',
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
    async detectSpecificTool(tool) {
        const detectedProcesses = [];
        const detectedWindows = [];
        const detectionMethods = [];
        for (const processName of tool.processNames) {
            const isRunning = await this.isProcessRunning(processName);
            if (isRunning) {
                detectedProcesses.push(processName);
                detectionMethods.push('process');
            }
        }
        for (const windowTitle of tool.windowTitles) {
            const windowExists = await this.isWindowExists(windowTitle);
            if (windowExists) {
                detectedWindows.push(windowTitle);
                detectionMethods.push('window');
            }
        }
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
    async isProcessRunning(processName) {
        try {
            const { stdout } = await execAsync(`tasklist /FI "IMAGENAME eq ${processName}" /FO CSV`);
            return stdout.includes(processName);
        }
        catch (error) {
            console.error(`检测进程 ${processName} 失败:`, error);
            return false;
        }
    }
    async isWindowExists(windowTitle) {
        try {
            const command = `powershell "Get-Process | Where-Object {$_.MainWindowTitle -like '*${windowTitle}*'} | Select-Object -First 1"`;
            const { stdout } = await execAsync(command);
            return stdout.trim().length > 0 && !stdout.includes('ProcessName');
        }
        catch (error) {
            console.error(`检测窗口 ${windowTitle} 失败:`, error);
            return false;
        }
    }
    async isRegistryKeyExists(registryKey) {
        try {
            const command = `reg query "${registryKey}" 2>nul`;
            const { stdout } = await execAsync(command);
            return stdout.trim().length > 0;
        }
        catch (error) {
            return false;
        }
    }
    async detectGameInjection(gameProcessId) {
        const suspiciousDlls = [];
        const injectionMethods = [];
        try {
            const command = `powershell "Get-Process -Id ${gameProcessId} | Select-Object -ExpandProperty Modules | Select-Object ModuleName, FileName"`;
            const { stdout } = await execAsync(command);
            const lines = stdout.split('\n').filter(line => line.trim());
            for (const line of lines) {
                const dllPath = line.trim();
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
        }
        catch (error) {
            console.error('检测游戏注入失败:', error);
            return {
                isInjected: false,
                suspiciousDlls: [],
                injectionMethods: []
            };
        }
    }
    isSuspiciousDll(dllPath) {
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
    async detectDriverLevelFilters() {
        const detectedFilters = [];
        try {
            const nvidiaFilters = await this.detectNvidiaFilters();
            detectedFilters.push(...nvidiaFilters);
            const amdFilters = await this.detectAmdFilters();
            detectedFilters.push(...amdFilters);
            return {
                hasDriverFilters: detectedFilters.length > 0,
                detectedFilters
            };
        }
        catch (error) {
            console.error('检测驱动级滤镜失败:', error);
            return {
                hasDriverFilters: false,
                detectedFilters: []
            };
        }
    }
    async detectNvidiaFilters() {
        const filters = [];
        try {
            const nvidiaKey = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\NVIDIA Corporation\\Global\\NVTweak';
            const keyExists = await this.isRegistryKeyExists(nvidiaKey);
            if (keyExists) {
                filters.push('NVIDIA 控制面板滤镜');
            }
            const geforceKey = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\NVIDIA Corporation\\Global\\GeForceExperience\\ANSEL';
            const anselExists = await this.isRegistryKeyExists(geforceKey);
            if (anselExists) {
                filters.push('NVIDIA Ansel 滤镜');
            }
        }
        catch (error) {
            console.error('检测 NVIDIA 滤镜失败:', error);
        }
        return filters;
    }
    async detectAmdFilters() {
        const filters = [];
        try {
            const amdKey = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\AMD\\CN';
            const keyExists = await this.isRegistryKeyExists(amdKey);
            if (keyExists) {
                filters.push('AMD Radeon 滤镜');
            }
        }
        catch (error) {
            console.error('检测 AMD 滤镜失败:', error);
        }
        return filters;
    }
    async generateFilterReport() {
        const detectedTools = await this.detectAllFilterTools();
        const driverFilters = await this.detectDriverLevelFilters();
        const highRiskTools = detectedTools.filter(tool => tool.riskLevel === 'high').length;
        const mediumRiskTools = detectedTools.filter(tool => tool.riskLevel === 'medium').length;
        const lowRiskTools = detectedTools.filter(tool => tool.riskLevel === 'low').length;
        const recommendations = [];
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
    startFilterMonitoring(callback, interval = 30000) {
        const monitor = async () => {
            try {
                const report = await this.generateFilterReport();
                callback(report);
            }
            catch (error) {
                console.error('滤镜监控失败:', error);
            }
        };
        monitor();
        return setInterval(monitor, interval);
    }
    stopFilterMonitoring(monitorId) {
        clearInterval(monitorId);
    }
}
