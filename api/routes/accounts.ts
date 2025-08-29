// 账号管理API路由
import express, { Response } from 'express';
import { DatabaseService } from '../../src/services/DatabaseService.js';
import { Account, CreateAccountRequest, UpdateAccountRequest, ExtendedRequest } from '../types/index.js';

const router = express.Router();

// 获取所有账号
router.get('/', async (req: ExtendedRequest, res: Response) => {
  try {
    const dbService = req.dbService;
    const accounts = await dbService.getAccounts();
    
    res.json({
      success: true,
      data: accounts
    });
  } catch (error) {
    console.error('获取账号列表失败:', error);
    res.status(500).json({
      success: false,
      message: '获取账号列表失败'
    });
  }
});

// 根据ID获取账号
router.get('/:id', async (req: ExtendedRequest, res: Response) => {
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
  } catch (error) {
    console.error('获取账号失败:', error);
    res.status(500).json({
      success: false,
      message: '获取账号失败'
    });
  }
});

// 创建新账号
router.post('/', async (req: ExtendedRequest, res: Response) => {
  try {
    const { name, gameAccount, isActive = true }: CreateAccountRequest = req.body;
    
    // 验证必填字段
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
  } catch (error) {
    console.error('创建账号失败:', error);
    res.status(500).json({
      success: false,
      message: '创建账号失败'
    });
  }
});

// 更新账号
router.put('/:id', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const updateData: UpdateAccountRequest = req.body;
    const dbService = req.dbService;
    
    // 检查账号是否存在
    const existingAccount = await dbService.getAccountById(id);
    if (!existingAccount) {
      return res.status(404).json({
        success: false,
        message: '账号不存在'
      });
    }
    
    const success = await dbService.updateAccount(id, updateData);
    
    if (success) {
      const updatedAccount = await dbService.getAccountById(id);
      res.json({
        success: true,
        data: updatedAccount,
        message: '账号更新成功'
      });
    } else {
      res.status(400).json({
        success: false,
        message: '账号更新失败'
      });
    }
  } catch (error) {
    console.error('更新账号失败:', error);
    res.status(500).json({
      success: false,
      message: '更新账号失败'
    });
  }
});

// 删除账号
router.delete('/:id', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const dbService = req.dbService;
    
    // 检查账号是否存在
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
    } else {
      res.status(400).json({
        success: false,
        message: '账号删除失败'
      });
    }
  } catch (error) {
    console.error('删除账号失败:', error);
    res.status(500).json({
      success: false,
      message: '删除账号失败'
    });
  }
});

// 更新账号最后登录时间
router.post('/:id/login', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const dbService: DatabaseService = req.dbService;
    
    const success = await dbService.updateAccount(id, {
      lastLoginAt: new Date()
    });
    
    if (success) {
      res.json({
        success: true,
        message: '登录时间更新成功'
      });
    } else {
      res.status(404).json({
        success: false,
        message: '账号不存在'
      });
    }
  } catch (error) {
    console.error('更新登录时间失败:', error);
    res.status(500).json({
      success: false,
      message: '更新登录时间失败'
    });
  }
});

export { router as accountRoutes };