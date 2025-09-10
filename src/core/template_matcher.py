"""模板匹配系统模块.

提供基于OpenCV的模板匹配功能，用于在游戏截图中识别UI元素。
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import logging
from enum import Enum

from src.exceptions.automation_exceptions import TemplateMatchError
from src.config.config_manager import ConfigManager


class MatchMethod(Enum):
    """模板匹配方法枚举."""
    TM_CCOEFF_NORMED = cv2.TM_CCOEFF_NORMED
    TM_CCORR_NORMED = cv2.TM_CCORR_NORMED
    TM_SQDIFF_NORMED = cv2.TM_SQDIFF_NORMED


@dataclass
class MatchResult:
    """匹配结果数据类."""
    found: bool
    confidence: float
    position: Optional[Tuple[int, int]] = None
    region: Optional[Tuple[int, int, int, int]] = None  # (x, y, width, height)
    template_name: Optional[str] = None
    match_method: Optional[MatchMethod] = None


@dataclass
class TemplateConfig:
    """模板配置数据类."""
    name: str
    path: str
    threshold: float = 0.8
    match_method: MatchMethod = MatchMethod.TM_CCOEFF_NORMED
    scale_range: Tuple[float, float] = (0.8, 1.2)
    rotation_range: Tuple[int, int] = (-5, 5)
    enabled: bool = True


class TemplateMatcher:
    """模板匹配器.
    
    提供高精度的模板匹配功能，支持多尺度、旋转匹配。
    """
    
    def __init__(self, config_manager: ConfigManager):
        """初始化模板匹配器.
        
        Args:
            config_manager: 配置管理器
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # 模板缓存
        self._template_cache: Dict[str, np.ndarray] = {}
        self._template_configs: Dict[str, TemplateConfig] = {}
        
        # 匹配配置
        self.default_threshold = 0.8
        self.default_method = MatchMethod.TM_CCOEFF_NORMED
        
        # 加载模板配置
        self._load_template_configs()
    
    def _load_template_configs(self):
        """加载模板配置."""
        try:
            template_config = self.config_manager.get_config('templates', {})
            
            for name, config in template_config.items():
                self._template_configs[name] = TemplateConfig(
                    name=name,
                    path=config.get('path', ''),
                    threshold=config.get('threshold', 0.8),
                    match_method=MatchMethod(config.get('match_method', cv2.TM_CCOEFF_NORMED)),
                    scale_range=tuple(config.get('scale_range', [0.8, 1.2])),
                    rotation_range=tuple(config.get('rotation_range', [-5, 5])),
                    enabled=config.get('enabled', True)
                )
                
        except Exception as e:
            self.logger.warning(f"加载模板配置失败: {e}")
    
    def load_template(self, template_name: str, template_path: Optional[str] = None) -> bool:
        """加载模板图像.
        
        Args:
            template_name: 模板名称
            template_path: 模板路径，如果为None则从配置中获取
            
        Returns:
            bool: 是否加载成功
        """
        try:
            if template_path is None:
                if template_name not in self._template_configs:
                    self.logger.error(f"未找到模板配置: {template_name}")
                    return False
                template_path = self._template_configs[template_name].path
            
            # 检查文件是否存在
            if not Path(template_path).exists():
                self.logger.error(f"模板文件不存在: {template_path}")
                return False
            
            # 加载图像
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            if template is None:
                self.logger.error(f"无法加载模板图像: {template_path}")
                return False
            
            self._template_cache[template_name] = template
            self.logger.debug(f"成功加载模板: {template_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"加载模板失败 {template_name}: {e}")
            return False
    
    def match_template(self, 
                      screenshot: np.ndarray, 
                      template_name: str,
                      threshold: Optional[float] = None,
                      method: Optional[MatchMethod] = None,
                      region: Optional[Tuple[int, int, int, int]] = None) -> MatchResult:
        """匹配模板.
        
        Args:
            screenshot: 截图图像
            template_name: 模板名称
            threshold: 匹配阈值
            method: 匹配方法
            region: 搜索区域 (x, y, width, height)
            
        Returns:
            MatchResult: 匹配结果
        """
        try:
            # 检查模板是否已加载
            if template_name not in self._template_cache:
                if not self.load_template(template_name):
                    return MatchResult(found=False, confidence=0.0)
            
            template = self._template_cache[template_name]
            
            # 获取配置
            config = self._template_configs.get(template_name)
            if threshold is None:
                threshold = config.threshold if config else self.default_threshold
            if method is None:
                method = config.match_method if config else self.default_method
            
            # 裁剪搜索区域
            search_image = screenshot
            offset_x, offset_y = 0, 0
            
            if region:
                x, y, w, h = region
                search_image = screenshot[y:y+h, x:x+w]
                offset_x, offset_y = x, y
            
            # 执行模板匹配
            result = cv2.matchTemplate(search_image, template, method.value)
            
            # 获取最佳匹配位置
            if method == MatchMethod.TM_SQDIFF_NORMED:
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                confidence = 1.0 - min_val
                match_loc = min_loc
            else:
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                confidence = max_val
                match_loc = max_loc
            
            # 检查是否满足阈值
            if confidence >= threshold:
                # 计算实际位置（加上偏移量）
                actual_x = match_loc[0] + offset_x
                actual_y = match_loc[1] + offset_y
                
                # 计算模板中心位置
                template_h, template_w = template.shape[:2]
                center_x = actual_x + template_w // 2
                center_y = actual_y + template_h // 2
                
                return MatchResult(
                    found=True,
                    confidence=confidence,
                    position=(center_x, center_y),
                    region=(actual_x, actual_y, template_w, template_h),
                    template_name=template_name,
                    match_method=method
                )
            else:
                return MatchResult(
                    found=False,
                    confidence=confidence,
                    template_name=template_name,
                    match_method=method
                )
                
        except Exception as e:
            self.logger.error(f"模板匹配失败 {template_name}: {e}")
            raise TemplateMatchError(f"模板匹配失败: {e}")
    
    def match_multiple_templates(self, 
                               screenshot: np.ndarray,
                               template_names: List[str],
                               threshold: Optional[float] = None,
                               region: Optional[Tuple[int, int, int, int]] = None) -> List[MatchResult]:
        """匹配多个模板.
        
        Args:
            screenshot: 截图图像
            template_names: 模板名称列表
            threshold: 匹配阈值
            region: 搜索区域
            
        Returns:
            List[MatchResult]: 匹配结果列表
        """
        results = []
        
        for template_name in template_names:
            try:
                result = self.match_template(
                    screenshot, template_name, threshold, region=region
                )
                results.append(result)
            except Exception as e:
                self.logger.error(f"匹配模板失败 {template_name}: {e}")
                results.append(MatchResult(
                    found=False, 
                    confidence=0.0, 
                    template_name=template_name
                ))
        
        return results
    
    def find_all_matches(self, 
                        screenshot: np.ndarray,
                        template_name: str,
                        threshold: Optional[float] = None,
                        region: Optional[Tuple[int, int, int, int]] = None) -> List[MatchResult]:
        """查找所有匹配项.
        
        Args:
            screenshot: 截图图像
            template_name: 模板名称
            threshold: 匹配阈值
            region: 搜索区域
            
        Returns:
            List[MatchResult]: 所有匹配结果
        """
        try:
            # 检查模板是否已加载
            if template_name not in self._template_cache:
                if not self.load_template(template_name):
                    return []
            
            template = self._template_cache[template_name]
            
            # 获取配置
            config = self._template_configs.get(template_name)
            if threshold is None:
                threshold = config.threshold if config else self.default_threshold
            
            method = config.match_method if config else self.default_method
            
            # 裁剪搜索区域
            search_image = screenshot
            offset_x, offset_y = 0, 0
            
            if region:
                x, y, w, h = region
                search_image = screenshot[y:y+h, x:x+w]
                offset_x, offset_y = x, y
            
            # 执行模板匹配
            result = cv2.matchTemplate(search_image, template, method.value)
            
            # 查找所有满足阈值的位置
            if method == MatchMethod.TM_SQDIFF_NORMED:
                locations = np.where(result <= (1.0 - threshold))
                confidences = 1.0 - result[locations]
            else:
                locations = np.where(result >= threshold)
                confidences = result[locations]
            
            matches = []
            template_h, template_w = template.shape[:2]
            
            for i, (y, x) in enumerate(zip(locations[0], locations[1])):
                # 计算实际位置
                actual_x = x + offset_x
                actual_y = y + offset_y
                
                # 计算中心位置
                center_x = actual_x + template_w // 2
                center_y = actual_y + template_h // 2
                
                matches.append(MatchResult(
                    found=True,
                    confidence=float(confidences[i]),
                    position=(center_x, center_y),
                    region=(actual_x, actual_y, template_w, template_h),
                    template_name=template_name,
                    match_method=method
                ))
            
            # 按置信度排序
            matches.sort(key=lambda x: x.confidence, reverse=True)
            return matches
            
        except Exception as e:
            self.logger.error(f"查找所有匹配项失败 {template_name}: {e}")
            return []
    
    def match_with_scale(self, 
                        screenshot: np.ndarray,
                        template_name: str,
                        scale_range: Tuple[float, float] = (0.8, 1.2),
                        scale_step: float = 0.1,
                        threshold: Optional[float] = None) -> MatchResult:
        """多尺度模板匹配.
        
        Args:
            screenshot: 截图图像
            template_name: 模板名称
            scale_range: 缩放范围
            scale_step: 缩放步长
            threshold: 匹配阈值
            
        Returns:
            MatchResult: 最佳匹配结果
        """
        try:
            if template_name not in self._template_cache:
                if not self.load_template(template_name):
                    return MatchResult(found=False, confidence=0.0)
            
            template = self._template_cache[template_name]
            best_result = MatchResult(found=False, confidence=0.0)
            
            # 获取配置
            config = self._template_configs.get(template_name)
            if threshold is None:
                threshold = config.threshold if config else self.default_threshold
            
            # 尝试不同的缩放比例
            scale = scale_range[0]
            while scale <= scale_range[1]:
                # 缩放模板
                scaled_template = cv2.resize(
                    template, 
                    None, 
                    fx=scale, 
                    fy=scale, 
                    interpolation=cv2.INTER_CUBIC
                )
                
                # 执行匹配
                method = config.match_method if config else self.default_method
                result = cv2.matchTemplate(screenshot, scaled_template, method.value)
                
                # 获取最佳匹配
                if method == MatchMethod.TM_SQDIFF_NORMED:
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    confidence = 1.0 - min_val
                    match_loc = min_loc
                else:
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    confidence = max_val
                    match_loc = max_loc
                
                # 更新最佳结果
                if confidence > best_result.confidence and confidence >= threshold:
                    template_h, template_w = scaled_template.shape[:2]
                    center_x = match_loc[0] + template_w // 2
                    center_y = match_loc[1] + template_h // 2
                    
                    best_result = MatchResult(
                        found=True,
                        confidence=confidence,
                        position=(center_x, center_y),
                        region=(match_loc[0], match_loc[1], template_w, template_h),
                        template_name=template_name,
                        match_method=method
                    )
                
                scale += scale_step
            
            return best_result
            
        except Exception as e:
            self.logger.error(f"多尺度匹配失败 {template_name}: {e}")
            return MatchResult(found=False, confidence=0.0)
    
    def clear_cache(self):
        """清空模板缓存."""
        self._template_cache.clear()
        self.logger.debug("模板缓存已清空")
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """获取模板信息.
        
        Args:
            template_name: 模板名称
            
        Returns:
            Optional[Dict[str, Any]]: 模板信息
        """
        if template_name not in self._template_configs:
            return None
        
        config = self._template_configs[template_name]
        info = {
            'name': config.name,
            'path': config.path,
            'threshold': config.threshold,
            'match_method': config.match_method.name,
            'scale_range': config.scale_range,
            'rotation_range': config.rotation_range,
            'enabled': config.enabled,
            'loaded': template_name in self._template_cache
        }
        
        if template_name in self._template_cache:
            template = self._template_cache[template_name]
            info['size'] = template.shape[:2]
        
        return info
    
    def list_templates(self) -> List[str]:
        """列出所有可用的模板.
        
        Returns:
            List[str]: 模板名称列表
        """
        return list(self._template_configs.keys())