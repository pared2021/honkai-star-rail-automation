import express from 'express';
const router = express.Router();
router.get('/', async (req, res) => {
    try {
        const dbService = req.dbService;
        const accounts = await dbService.getAccounts();
        res.json({
            success: true,
            data: accounts
        });
    }
    catch (error) {
        console.error('获取账号列表失败:', error);
        res.status(500).json({
            success: false,
            message: '获取账号列表失败'
        });
    }
});
router.get('/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const dbService = req.dbService;
        const account = await dbService.getAccountById(id);
        if (!account) {
            return res.status(404).json({
                success: false,
                message: '账号不存在'
            });
        }
        res.json({
            success: true,
            data: account
        });
    }
    catch (error) {
        console.error('获取账号失败:', error);
        res.status(500).json({
            success: false,
            message: '获取账号失败'
        });
    }
});
router.post('/', async (req, res) => {
    try {
        const { name, gameAccount, isActive = true } = req.body;
        if (!name || !gameAccount) {
            return res.status(400).json({
                success: false,
                message: '账号名称和游戏账号为必填项'
            });
        }
        const dbService = req.dbService;
        const account = await dbService.createAccount({
            name,
            gameAccount,
            isActive
        });
        res.status(201).json({
            success: true,
            data: account,
            message: '账号创建成功'
        });
    }
    catch (error) {
        console.error('创建账号失败:', error);
        res.status(500).json({
            success: false,
            message: '创建账号失败'
        });
    }
});
router.put('/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const updates = req.body;
        const dbService = req.dbService;
        const existingAccount = await dbService.getAccountById(id);
        if (!existingAccount) {
            return res.status(404).json({
                success: false,
                message: '账号不存在'
            });
        }
        const success = await dbService.updateAccount(id, updates);
        if (success) {
            const updatedAccount = await dbService.getAccountById(id);
            res.json({
                success: true,
                data: updatedAccount,
                message: '账号更新成功'
            });
        }
        else {
            res.status(400).json({
                success: false,
                message: '账号更新失败'
            });
        }
    }
    catch (error) {
        console.error('更新账号失败:', error);
        res.status(500).json({
            success: false,
            message: '更新账号失败'
        });
    }
});
router.delete('/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const dbService = req.dbService;
        const existingAccount = await dbService.getAccountById(id);
        if (!existingAccount) {
            return res.status(404).json({
                success: false,
                message: '账号不存在'
            });
        }
        const success = await dbService.deleteAccount(id);
        if (success) {
            res.json({
                success: true,
                message: '账号删除成功'
            });
        }
        else {
            res.status(400).json({
                success: false,
                message: '账号删除失败'
            });
        }
    }
    catch (error) {
        console.error('删除账号失败:', error);
        res.status(500).json({
            success: false,
            message: '删除账号失败'
        });
    }
});
router.post('/:id/login', async (req, res) => {
    try {
        const { id } = req.params;
        const dbService = req.dbService;
        const success = await dbService.updateAccount(id, {
            lastLoginAt: new Date()
        });
        if (success) {
            res.json({
                success: true,
                message: '登录时间更新成功'
            });
        }
        else {
            res.status(404).json({
                success: false,
                message: '账号不存在'
            });
        }
    }
    catch (error) {
        console.error('更新登录时间失败:', error);
        res.status(500).json({
            success: false,
            message: '更新登录时间失败'
        });
    }
});
export { router as accountRoutes };
