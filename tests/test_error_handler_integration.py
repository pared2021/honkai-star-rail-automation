#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理集成测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import asyncio
from unittest.mock import Mock, patch


class TestErrorHandlerIntegration:
    """错误处理集成测试类"""
    
    def test_error_handler_initialization(self):
        """测试错误处理器初始化"""
        from core.error_handler import ErrorHandler
        error_handler = ErrorHandler()
        assert error_handler is not None
        assert hasattr(error_handler, 'handle_error')
        assert hasattr(error_handler, 'get_error_info')
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """测试错误处理工作流"""
        from core.error_handler import ErrorHandler
        error_handler = ErrorHandler()
        
        # 模拟一个异常
        test_exception = Exception("测试异常")
        
        # 处理错误
        error_info = await error_handler.handle_error(test_exception, "test_task", "test_type", {"test": "context"})
        
        # 验证错误信息
        assert error_info is not None
        assert error_info.error_id is not None
        assert error_info.error_type == "Exception"
        assert error_info.error_message == "测试异常"
        assert error_info.task_id == "test_task"
        assert error_info.task_type == "test_type"
        
        # 验证可以获取错误信息
        retrieved_error = error_handler.get_error_info(error_info.error_id)
        assert retrieved_error is not None
        assert retrieved_error.error_id == error_info.error_id
    
    def test_error_statistics(self):
        """测试错误统计功能"""
        from core.error_handler import ErrorHandler
        error_handler = ErrorHandler()
        
        # 获取统计信息
        stats = error_handler.get_error_statistics()
        assert stats is not None
        assert 'total_errors' in stats
        assert 'resolved_errors' in stats
        assert 'resolution_rate' in stats


if __name__ == '__main__':
    pytest.main([__file__, '-v'])