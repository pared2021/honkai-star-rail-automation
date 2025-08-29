import express from 'express';
import cors from 'cors';
import { DatabaseService } from '../src/services/DatabaseService.js';
import { ApiService } from '../src/services/ApiService.js';
import { StrategyDataInitializer } from '../src/services/StrategyDataInitializer.js';
import { accountRoutes } from './routes/accounts.js';
import { taskRoutes } from './routes/tasks.js';
import { gameRoutes } from './routes/game.js';
import { statsRoutes } from './routes/stats.js';
const app = express();
const PORT = process.env.PORT || 3001;
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
let dbService;
let apiService;
let strategyInitializer;
async function initializeServices() {
    try {
        dbService = new DatabaseService();
        await dbService.initialize();
        apiService = new ApiService();
        await apiService.initialize();
        strategyInitializer = new StrategyDataInitializer(dbService);
        await strategyInitializer.initializePresetData();
        console.log('服务初始化完成');
    }
    catch (error) {
        console.error('服务初始化失败:', error);
        process.exit(1);
    }
}
app.use((req, res, next) => {
    req.dbService = dbService;
    req.apiService = apiService;
    next();
});
app.use('/api/accounts', accountRoutes);
app.use('/api/tasks', taskRoutes);
app.use('/api/stats', statsRoutes);
app.use('/api/game', gameRoutes);
app.get('/api/health', (req, res) => {
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        version: '1.0.0'
    });
});
app.use((err, req, res, next) => {
    console.error('API错误:', err);
    res.status(500).json({
        success: false,
        message: '服务器内部错误',
        error: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
});
app.use('*', (req, res) => {
    res.status(404).json({
        success: false,
        message: '接口不存在'
    });
});
async function startServer() {
    await initializeServices();
    app.listen(PORT, () => {
        console.log(`API服务器已启动: http://localhost:${PORT}`);
        console.log(`健康检查: http://localhost:${PORT}/api/health`);
    });
}
process.on('SIGTERM', async () => {
    console.log('正在关闭服务器...');
    if (dbService) {
        await dbService.close();
    }
    process.exit(0);
});
process.on('SIGINT', async () => {
    console.log('正在关闭服务器...');
    if (dbService) {
        await dbService.close();
    }
    process.exit(0);
});
if (import.meta.url.endsWith('index.js')) {
    startServer().catch(console.error);
}
export { app, dbService, apiService };
