"""pytest配置文件

全局测试配置和fixture定义。
"""

import pytest
import asyncio
import tempfile
import os
from typing import Generator, AsyncGenerator

# 配置asyncio事件循环
@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于整个测试会话"""
    import threading
    import signal
    import time
    
    # 设置事件循环策略
    if os.name == 'nt':  # Windows
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        yield loop
    finally:
        # 强制清理所有资源
        try:
            # 1. 取消所有异步任务
            pending = asyncio.all_tasks(loop)
            if pending:
                for task in pending:
                    if not task.done():
                        task.cancel()
                
                # 等待任务取消，设置超时
                try:
                    loop.run_until_complete(
                        asyncio.wait_for(
                            asyncio.gather(*pending, return_exceptions=True),
                            timeout=5.0
                        )
                    )
                except asyncio.TimeoutError:
                    print("警告: 某些异步任务未能在超时时间内取消")
            
            # 2. 强制停止事件循环
            if loop.is_running():
                loop.stop()
            
            # 3. 等待循环停止
            timeout = 3.0
            start_time = time.time()
            while loop.is_running() and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            # 4. 关闭事件循环
            if not loop.is_closed():
                loop.close()
                
        except Exception as e:
            print(f"事件循环清理时发生错误: {e}")
        
        # 5. 强制清理所有活动线程（除主线程外）
        try:
            main_thread = threading.main_thread()
            for thread in threading.enumerate():
                if thread != main_thread and thread.is_alive():
                    print(f"强制终止线程: {thread.name}")
                    # 对于daemon线程，设置为daemon以便程序退出时自动终止
                    if hasattr(thread, '_stop'):
                        thread._stop()
        except Exception as e:
            print(f"线程清理时发生错误: {e}")
        
        # 6. 强制垃圾回收
        import gc
        gc.collect()
        
        # 7. 最后的清理
        try:
            # 重置asyncio状态
            asyncio.set_event_loop(None)
        except Exception:
            pass


@pytest.fixture
def temp_db_path() -> Generator[str, None, None]:
    """创建临时数据库文件路径"""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_path = db_file.name
    db_file.close()
    
    yield db_path
    
    # 清理
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """创建临时目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    
    # 清理
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


# 测试标记
pytest_plugins = []

# 自定义标记
def pytest_configure(config):
    """配置自定义标记"""
    config.addinivalue_line(
        "markers", "unit: 标记单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 标记集成测试"
    )
    config.addinivalue_line(
        "markers", "performance: 标记性能测试"
    )
    config.addinivalue_line(
        "markers", "slow: 标记慢速测试"
    )
    config.addinivalue_line(
        "markers", "database: 标记需要数据库的测试"
    )
    config.addinivalue_line(
        "markers", "automation: 标记自动化相关测试"
    )


# 测试收集配置
def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    # 为慢速测试添加标记
    for item in items:
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "test_automation" in item.nodeid or "automation" in item.nodeid:
            item.add_marker(pytest.mark.automation)
        if any(keyword in item.nodeid for keyword in ["repository", "database", "db"]):
            item.add_marker(pytest.mark.database)


# 异步测试支持
@pytest.fixture(scope="function")
async def async_test_client():
    """异步测试客户端"""
    # 这里可以添加异步测试客户端的设置
    yield


# 日志配置
@pytest.fixture(autouse=True)
def configure_logging(caplog):
    """配置测试日志"""
    import logging
    
    # 设置日志级别
    caplog.set_level(logging.INFO)
    
    # 配置特定模块的日志级别
    logging.getLogger("src.repositories").setLevel(logging.WARNING)
    logging.getLogger("src.core").setLevel(logging.INFO)
    logging.getLogger("src.services").setLevel(logging.INFO)


# 测试数据清理
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """自动清理测试数据"""
    yield
    
    # 测试后清理
    import gc
    gc.collect()


# 强制进程清理
@pytest.fixture(autouse=True, scope="function")
def force_cleanup_processes():
    """强制清理进程和资源"""
    import psutil
    import threading
    import time
    
    # 记录测试开始时的进程和线程状态
    initial_threads = set(threading.enumerate())
    current_process = psutil.Process()
    initial_children = current_process.children(recursive=True)
    
    yield
    
    # 测试结束后强制清理
    try:
        # 1. 清理子进程
        current_children = current_process.children(recursive=True)
        new_children = [p for p in current_children if p not in initial_children]
        
        for child in new_children:
            try:
                print(f"终止子进程: {child.pid} - {child.name()}")
                child.terminate()
                child.wait(timeout=3)
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            except Exception as e:
                print(f"清理子进程时出错: {e}")
        
        # 2. 清理新创建的线程
        current_threads = set(threading.enumerate())
        new_threads = current_threads - initial_threads
        
        for thread in new_threads:
            if thread.is_alive() and thread != threading.current_thread():
                try:
                    print(f"等待线程结束: {thread.name}")
                    thread.join(timeout=2)
                    if thread.is_alive():
                        print(f"线程 {thread.name} 未能正常结束")
                        # 对于daemon线程，强制设置为daemon
                        if not thread.daemon:
                            thread.daemon = True
                except Exception as e:
                    print(f"清理线程时出错: {e}")
        
        # 3. 强制垃圾回收
        import gc
        gc.collect()
        
        # 4. 清理asyncio相关资源
        try:
            loop = asyncio.get_event_loop()
            if loop and not loop.is_closed():
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    if not task.done():
                        task.cancel()
        except RuntimeError:
            # 没有事件循环运行
            pass
        except Exception as e:
            print(f"清理asyncio资源时出错: {e}")
            
    except Exception as e:
        print(f"强制清理过程中出错: {e}")


# Mock配置
@pytest.fixture
def mock_automation_operations():
    """Mock自动化操作"""
    from unittest.mock import Mock, AsyncMock
    from src.services.automation_application_service import WindowInfo, ElementMatch
    
    mocks = {
        'detect_game_window': AsyncMock(return_value=WindowInfo(
            window_id="mock_window",
            title="Mock Game Window",
            rect={'x': 0, 'y': 0, 'width': 1920, 'height': 1080},
            process_id=1234,
            is_active=True
        )),
        'take_screenshot': AsyncMock(return_value="mock_screenshot.png"),
        'find_element': AsyncMock(return_value=ElementMatch(
            element_id="mock_element",
            confidence=0.95,
            position={'x': 100, 'y': 200},
            size={'width': 80, 'height': 30}
        )),
        'click_element': AsyncMock(return_value=True),
        'input_text': AsyncMock(return_value=True),
        'wait_for_element': AsyncMock(return_value=ElementMatch(
            element_id="waited_element",
            confidence=0.90,
            position={'x': 150, 'y': 250},
            size={'width': 100, 'height': 40}
        )),
        'execute_automation_sequence': AsyncMock(return_value=True)
    }
    
    return mocks


# 性能测试配置
@pytest.fixture
def performance_config():
    """性能测试配置"""
    return {
        'max_task_creation_time': 0.1,  # 最大任务创建时间(秒)
        'max_database_operation_time': 0.05,  # 最大数据库操作时间(秒)
        'min_throughput': 1.0,  # 最小吞吐量(任务/秒)
        'max_memory_increase': 200,  # 最大内存增长(MB)
        'max_event_processing_time': 0.01,  # 最大事件处理时间(秒)
    }


# 测试环境信息
@pytest.fixture(scope="session")
def test_environment_info():
    """测试环境信息"""
    import platform
    import sys
    
    return {
        'platform': platform.platform(),
        'python_version': sys.version,
        'architecture': platform.architecture(),
        'processor': platform.processor(),
    }


# 测试报告钩子
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """测试结束后的总结报告"""
    if hasattr(terminalreporter, 'stats'):
        stats = terminalreporter.stats
        
        print("\n" + "="*60)
        print("测试执行总结")
        print("="*60)
        
        if 'passed' in stats:
            print(f"✅ 通过: {len(stats['passed'])} 个测试")
        
        if 'failed' in stats:
            print(f"❌ 失败: {len(stats['failed'])} 个测试")
        
        if 'skipped' in stats:
            print(f"⏭️  跳过: {len(stats['skipped'])} 个测试")
        
        if 'error' in stats:
            print(f"💥 错误: {len(stats['error'])} 个测试")
        
        print("="*60)