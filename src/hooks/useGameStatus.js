import { useState, useCallback } from 'react';
import { message } from 'antd';
export const useGameStatus = () => {
    const [gameStatus, setGameStatus] = useState(null);
    const [loading, setLoading] = useState(false);
    const [showGameDialog, setShowGameDialog] = useState(false);
    const checkGameStatus = useCallback(async () => {
        setLoading(true);
        try {
            const response = await fetch('/api/game/status');
            const data = await response.json();
            if (data.success) {
                const status = {
                    isRunning: data.data.isRunning,
                    processId: data.data.processId,
                    windowTitle: data.data.windowTitle,
                    lastCheck: new Date()
                };
                setGameStatus(status);
                return status;
            }
            else {
                throw new Error(data.message || '检测游戏状态失败');
            }
        }
        catch (error) {
            console.error('检测游戏状态失败:', error);
            const status = {
                isRunning: false,
                lastCheck: new Date()
            };
            setGameStatus(status);
            return status;
        }
        finally {
            setLoading(false);
        }
    }, []);
    const launchGame = useCallback(async () => {
        try {
            // 获取游戏设置
            const savedSettings = localStorage.getItem('app_settings');
            if (!savedSettings) {
                throw new Error('未找到游戏设置，请先在设置页面配置游戏路径');
            }
            const appSettings = JSON.parse(savedSettings);
            const gameSettings = appSettings.gameMonitorSettings;
            if (!gameSettings || !gameSettings.gamePath) {
                throw new Error('游戏路径未配置，请先在设置页面配置游戏路径');
            }
            const response = await fetch('/api/game/launch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    gamePath: gameSettings.gamePath,
                    startMonitoring: gameSettings.enableGameMonitoring || false
                })
            });
            const data = await response.json();
            if (data.success) {
                message.success('游戏启动成功');
                // 延迟检查游戏状态，确保游戏完全启动
                setTimeout(() => {
                    checkGameStatus();
                }, 3000);
            }
            else {
                throw new Error(data.message || '启动游戏失败');
            }
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : '启动游戏失败';
            message.error(errorMessage);
            throw error;
        }
    }, [checkGameStatus]);
    const checkAndPromptIfNeeded = useCallback(async (actionName = '执行此操作') => {
        const status = await checkGameStatus();
        if (!status.isRunning) {
            setShowGameDialog(true);
            return false; // 游戏未运行，需要用户确认
        }
        return true; // 游戏正在运行，可以继续操作
    }, [checkGameStatus]);
    return {
        gameStatus,
        loading,
        checkGameStatus,
        launchGame,
        showGameDialog,
        setShowGameDialog,
        checkAndPromptIfNeeded
    };
};
