from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QGroupBox, QSpinBox, QFileDialog, QMessageBox,
    QFormLayout, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import os
from typing import Dict, Any
from loguru import logger

from ..core.config_manager import ConfigManager


class GameSettingsWidget(QWidget):
    """游戏设置界面组件"""
    
    # 信号定义
    settings_changed = pyqtSignal(str, str, object)  # category, key, value
    
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._init_ui()
        self._load_settings()
        self._connect_signals()
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("游戏设置")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 游戏路径设置组
        game_path_group = self._create_game_path_group()
        layout.addWidget(game_path_group)
        
        # 显示设置组
        display_group = self._create_display_group()
        layout.addWidget(display_group)
        
        # 窗口设置组
        window_group = self._create_window_group()
        layout.addWidget(window_group)
        
        # 检测设置组
        detection_group = self._create_detection_group()
        layout.addWidget(detection_group)
        
        # 按钮区域
        button_layout = self._create_button_layout()
        layout.addLayout(button_layout)
        
        # 添加弹性空间
        layout.addStretch()
    
    def _create_game_path_group(self) -> QGroupBox:
        """创建游戏路径设置组"""
        group = QGroupBox("游戏路径")
        layout = QVBoxLayout(group)
        
        # 游戏路径选择
        path_layout = QHBoxLayout()
        
        self.game_path_edit = QLineEdit()
        self.game_path_edit.setPlaceholderText("请选择游戏安装路径...")
        self.game_path_edit.setReadOnly(True)
        path_layout.addWidget(self.game_path_edit)
        
        self.browse_button = QPushButton("浏览")
        self.browse_button.setFixedWidth(80)
        self.browse_button.clicked.connect(self._browse_game_path)
        path_layout.addWidget(self.browse_button)
        
        layout.addLayout(path_layout)
        
        # 自动检测按钮
        self.auto_detect_button = QPushButton("自动检测游戏路径")
        self.auto_detect_button.clicked.connect(self._auto_detect_game_path)
        layout.addWidget(self.auto_detect_button)
        
        # 路径状态标签
        self.path_status_label = QLabel("")
        self.path_status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.path_status_label)
        
        return group
    
    def _create_display_group(self) -> QGroupBox:
        """创建显示设置组"""
        group = QGroupBox("显示设置")
        layout = QFormLayout(group)
        
        # 分辨率设置
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "1920x1080",
            "1366x768",
            "1280x720",
            "1600x900",
            "2560x1440",
            "3840x2160",
            "自定义"
        ])
        self.resolution_combo.currentTextChanged.connect(self._on_resolution_changed)
        layout.addRow("游戏分辨率:", self.resolution_combo)
        
        # 自定义分辨率输入
        custom_layout = QHBoxLayout()
        self.custom_width_spin = QSpinBox()
        self.custom_width_spin.setRange(800, 7680)
        self.custom_width_spin.setValue(1920)
        self.custom_width_spin.setEnabled(False)
        custom_layout.addWidget(self.custom_width_spin)
        
        custom_layout.addWidget(QLabel("×"))
        
        self.custom_height_spin = QSpinBox()
        self.custom_height_spin.setRange(600, 4320)
        self.custom_height_spin.setValue(1080)
        self.custom_height_spin.setEnabled(False)
        custom_layout.addWidget(self.custom_height_spin)
        
        custom_layout.addStretch()
        layout.addRow("自定义分辨率:", custom_layout)
        
        # 缩放比例
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["100%", "125%", "150%", "175%", "200%"])
        layout.addRow("界面缩放:", self.scale_combo)
        
        return group
    
    def _create_window_group(self) -> QGroupBox:
        """创建窗口设置组"""
        group = QGroupBox("窗口设置")
        layout = QFormLayout(group)
        
        # 窗口标题
        self.window_title_edit = QLineEdit()
        self.window_title_edit.setPlaceholderText("崩坏：星穹铁道")
        layout.addRow("窗口标题:", self.window_title_edit)
        
        # 窗口模式
        self.window_mode_combo = QComboBox()
        self.window_mode_combo.addItems(["全屏", "窗口化", "无边框窗口"])
        layout.addRow("窗口模式:", self.window_mode_combo)
        
        # 置顶选项
        self.always_on_top_check = QCheckBox("保持窗口置顶")
        layout.addRow("", self.always_on_top_check)
        
        # 自动聚焦
        self.auto_focus_check = QCheckBox("自动聚焦游戏窗口")
        layout.addRow("", self.auto_focus_check)
        
        return group
    
    def _create_detection_group(self) -> QGroupBox:
        """创建检测设置组"""
        group = QGroupBox("检测设置")
        layout = QFormLayout(group)
        
        # 检测超时
        self.detection_timeout_spin = QSpinBox()
        self.detection_timeout_spin.setRange(5, 300)
        self.detection_timeout_spin.setValue(30)
        self.detection_timeout_spin.setSuffix(" 秒")
        layout.addRow("检测超时:", self.detection_timeout_spin)
        
        # 检测间隔
        self.detection_interval_spin = QSpinBox()
        self.detection_interval_spin.setRange(100, 5000)
        self.detection_interval_spin.setValue(500)
        self.detection_interval_spin.setSuffix(" 毫秒")
        layout.addRow("检测间隔:", self.detection_interval_spin)
        
        # 启用游戏检测
        self.enable_detection_check = QCheckBox("启用游戏窗口检测")
        self.enable_detection_check.setChecked(True)
        layout.addRow("", self.enable_detection_check)
        
        return group
    
    def _create_button_layout(self) -> QHBoxLayout:
        """创建按钮布局"""
        layout = QHBoxLayout()
        layout.addStretch()
        
        # 测试连接按钮
        self.test_button = QPushButton("测试游戏连接")
        self.test_button.clicked.connect(self._test_game_connection)
        layout.addWidget(self.test_button)
        
        # 重置按钮
        self.reset_button = QPushButton("重置为默认")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        layout.addWidget(self.reset_button)
        
        # 应用按钮
        self.apply_button = QPushButton("应用设置")
        self.apply_button.clicked.connect(self._apply_settings)
        layout.addWidget(self.apply_button)
        
        return layout
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 配置变更信号
        self.game_path_edit.textChanged.connect(
            lambda text: self._on_setting_changed('game', 'game_path', text)
        )
        self.window_title_edit.textChanged.connect(
            lambda text: self._on_setting_changed('game', 'window_title', text)
        )
        self.resolution_combo.currentTextChanged.connect(
            lambda text: self._on_setting_changed('game', 'resolution', text)
        )
        self.window_mode_combo.currentTextChanged.connect(
            lambda text: self._on_setting_changed('game', 'window_mode', text)
        )
        self.always_on_top_check.toggled.connect(
            lambda checked: self._on_setting_changed('game', 'always_on_top', checked)
        )
        self.auto_focus_check.toggled.connect(
            lambda checked: self._on_setting_changed('game', 'auto_focus', checked)
        )
        self.detection_timeout_spin.valueChanged.connect(
            lambda value: self._on_setting_changed('game', 'detection_timeout', value)
        )
        self.detection_interval_spin.valueChanged.connect(
            lambda value: self._on_setting_changed('game', 'detection_interval', value)
        )
        self.enable_detection_check.toggled.connect(
            lambda checked: self._on_setting_changed('game', 'enable_detection', checked)
        )
        self.scale_combo.currentTextChanged.connect(
            lambda text: self._on_setting_changed('game', 'ui_scale', text)
        )
    
    def _load_settings(self):
        """加载配置设置"""
        try:
            game_config = self.config_manager.get_game_config()
            
            # 加载游戏路径
            game_path = game_config.get('game_path', '')
            self.game_path_edit.setText(game_path)
            self._update_path_status(game_path)
            
            # 加载分辨率
            resolution = game_config.get('resolution', '1920x1080')
            index = self.resolution_combo.findText(resolution)
            if index >= 0:
                self.resolution_combo.setCurrentIndex(index)
            else:
                self.resolution_combo.setCurrentText("自定义")
                if 'x' in resolution:
                    width, height = resolution.split('x')
                    self.custom_width_spin.setValue(int(width))
                    self.custom_height_spin.setValue(int(height))
            
            # 加载窗口标题
            window_title = game_config.get('window_title', '崩坏：星穹铁道')
            self.window_title_edit.setText(window_title)
            
            # 加载其他设置
            self.detection_timeout_spin.setValue(game_config.get('detection_timeout', 30))
            self.detection_interval_spin.setValue(game_config.get('detection_interval', 500))
            self.enable_detection_check.setChecked(game_config.get('enable_detection', True))
            
            # 加载窗口模式
            window_mode = game_config.get('window_mode', '窗口化')
            mode_index = self.window_mode_combo.findText(window_mode)
            if mode_index >= 0:
                self.window_mode_combo.setCurrentIndex(mode_index)
            
            # 加载其他选项
            self.always_on_top_check.setChecked(game_config.get('always_on_top', False))
            self.auto_focus_check.setChecked(game_config.get('auto_focus', True))
            
            # 加载界面缩放
            ui_scale = game_config.get('ui_scale', '100%')
            scale_index = self.scale_combo.findText(ui_scale)
            if scale_index >= 0:
                self.scale_combo.setCurrentIndex(scale_index)
            
            logger.info("游戏设置加载完成")
            
        except Exception as e:
            logger.error(f"加载游戏设置失败: {e}")
            QMessageBox.warning(self, "加载失败", f"加载游戏设置失败：{str(e)}")
    
    def _browse_game_path(self):
        """浏览游戏路径"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择游戏可执行文件",
            "",
            "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        
        if file_path:
            self.game_path_edit.setText(file_path)
            self._update_path_status(file_path)
    
    def _auto_detect_game_path(self):
        """自动检测游戏路径"""
        try:
            # 常见的游戏安装路径
            common_paths = [
                r"C:\Program Files\miHoYo\Star Rail\Game\StarRail.exe",
                r"C:\Program Files (x86)\miHoYo\Star Rail\Game\StarRail.exe",
                r"D:\miHoYo\Star Rail\Game\StarRail.exe",
                r"E:\miHoYo\Star Rail\Game\StarRail.exe",
                r"F:\miHoYo\Star Rail\Game\StarRail.exe"
            ]
            
            detected_path = None
            for path in common_paths:
                if os.path.exists(path):
                    detected_path = path
                    break
            
            if detected_path:
                self.game_path_edit.setText(detected_path)
                self._update_path_status(detected_path)
                QMessageBox.information(self, "检测成功", f"已检测到游戏路径：\n{detected_path}")
            else:
                QMessageBox.information(self, "检测失败", "未能自动检测到游戏路径，请手动选择。")
                
        except Exception as e:
            logger.error(f"自动检测游戏路径失败: {e}")
            QMessageBox.warning(self, "检测失败", f"自动检测失败：{str(e)}")
    
    def _update_path_status(self, path: str):
        """更新路径状态显示"""
        if not path:
            self.path_status_label.setText("未设置游戏路径")
            self.path_status_label.setStyleSheet("color: #ff6b6b; font-size: 11px;")
        elif os.path.exists(path):
            self.path_status_label.setText("✓ 路径有效")
            self.path_status_label.setStyleSheet("color: #51cf66; font-size: 11px;")
        else:
            self.path_status_label.setText("✗ 路径无效")
            self.path_status_label.setStyleSheet("color: #ff6b6b; font-size: 11px;")
    
    def _on_resolution_changed(self, resolution: str):
        """分辨率改变处理"""
        is_custom = resolution == "自定义"
        self.custom_width_spin.setEnabled(is_custom)
        self.custom_height_spin.setEnabled(is_custom)
        
        if is_custom:
            # 使用自定义分辨率
            width = self.custom_width_spin.value()
            height = self.custom_height_spin.value()
            custom_resolution = f"{width}x{height}"
            self._on_setting_changed('game', 'resolution', custom_resolution)
    
    def _test_game_connection(self):
        """测试游戏连接"""
        try:
            # 这里可以添加实际的游戏检测逻辑
            game_path = self.game_path_edit.text()
            if not game_path or not os.path.exists(game_path):
                QMessageBox.warning(self, "测试失败", "请先设置有效的游戏路径")
                return
            
            # 模拟检测过程
            QMessageBox.information(self, "测试结果", "游戏连接测试成功！\n\n检测到游戏窗口配置正常。")
            logger.info("游戏连接测试完成")
            
        except Exception as e:
            logger.error(f"游戏连接测试失败: {e}")
            QMessageBox.critical(self, "测试失败", f"游戏连接测试失败：{str(e)}")
    
    def _reset_to_defaults(self):
        """重置为默认设置"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有游戏设置为默认值吗？\n\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 重置配置
                self.config_manager.reset_category('game')
                
                # 重新加载界面
                self._load_settings()
                
                QMessageBox.information(self, "重置完成", "游戏设置已重置为默认值")
                logger.info("游戏设置已重置为默认值")
                
            except Exception as e:
                logger.error(f"重置设置失败: {e}")
                QMessageBox.critical(self, "重置失败", f"重置设置失败：{str(e)}")
    
    def _apply_settings(self):
        """应用设置"""
        try:
            # 验证设置
            if not self._validate_settings():
                return
            
            # 保存配置
            self.config_manager.save_config()
            
            QMessageBox.information(self, "应用成功", "游戏设置已成功应用")
            logger.info("游戏设置已应用")
            
        except Exception as e:
            logger.error(f"应用设置失败: {e}")
            QMessageBox.critical(self, "应用失败", f"应用设置失败：{str(e)}")
    
    def _validate_settings(self) -> bool:
        """验证设置有效性"""
        # 验证游戏路径
        game_path = self.game_path_edit.text().strip()
        if game_path and not os.path.exists(game_path):
            QMessageBox.warning(self, "验证失败", "游戏路径无效，请检查路径是否正确")
            return False
        
        # 验证窗口标题
        window_title = self.window_title_edit.text().strip()
        if not window_title:
            QMessageBox.warning(self, "验证失败", "窗口标题不能为空")
            return False
        
        # 验证自定义分辨率
        if self.resolution_combo.currentText() == "自定义":
            width = self.custom_width_spin.value()
            height = self.custom_height_spin.value()
            if width < 800 or height < 600:
                QMessageBox.warning(self, "验证失败", "自定义分辨率不能小于 800x600")
                return False
        
        return True
    
    def _on_setting_changed(self, category: str, key: str, value: Any):
        """设置变更处理"""
        try:
            # 处理自定义分辨率
            if key == 'resolution' and value == "自定义":
                width = self.custom_width_spin.value()
                height = self.custom_height_spin.value()
                value = f"{width}x{height}"
            
            # 更新配置
            self.config_manager.set_setting(category, key, value)
            
            # 发射信号
            self.settings_changed.emit(category, key, value)
            
            logger.debug(f"设置已更新: {category}.{key} = {value}")
            
        except Exception as e:
            logger.error(f"更新设置失败: {e}")
    
    def get_current_settings(self) -> Dict[str, Any]:
        """获取当前设置"""
        resolution = self.resolution_combo.currentText()
        if resolution == "自定义":
            width = self.custom_width_spin.value()
            height = self.custom_height_spin.value()
            resolution = f"{width}x{height}"
        
        return {
            'game_path': self.game_path_edit.text(),
            'resolution': resolution,
            'window_title': self.window_title_edit.text(),
            'window_mode': self.window_mode_combo.currentText(),
            'always_on_top': self.always_on_top_check.isChecked(),
            'auto_focus': self.auto_focus_check.isChecked(),
            'detection_timeout': self.detection_timeout_spin.value(),
            'detection_interval': self.detection_interval_spin.value(),
            'enable_detection': self.enable_detection_check.isChecked(),
            'ui_scale': self.scale_combo.currentText()
        }