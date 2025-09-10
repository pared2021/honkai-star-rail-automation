"""OCR文本识别模块.

提供OCR文本识别功能。"""

import cv2
import numpy as np
import io
import logging
from typing import Any, Dict, List, Optional, Tuple

try:
    import pytesseract
    from PIL import Image as PILImage
except ImportError:
    pytesseract = None
    PILImage = None


class OCRDetector:
    """OCR文本识别器."""

    def __init__(self):
        """初始化OCR检测器."""
        self.logger = logging.getLogger(__name__)
        self.enable_ocr: bool = True
        self.ocr_config: str = '--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        
    def recognize_text(self, image_region: Optional[np.ndarray] = None, 
                      region: Optional[Tuple[int, int, int, int]] = None,
                      screenshot_data: Optional[bytes] = None) -> Optional[str]:
        """使用OCR识别图像中的文本.
        
        Args:
            image_region: 要识别的图像区域（numpy数组）
            region: 屏幕区域坐标 (x, y, width, height)
            screenshot_data: 截图数据
            
        Returns:
            Optional[str]: 识别到的文本，失败返回None
        """
        if not self.enable_ocr or not pytesseract:
            self.logger.warning("OCR功能未启用或pytesseract未安装")
            return None
            
        try:
            # 获取要识别的图像
            if image_region is not None:
                target_image = image_region
            elif screenshot_data and region:
                # 从截图数据中提取指定区域
                img_pil = PILImage.open(io.BytesIO(screenshot_data))
                x, y, w, h = region
                cropped = img_pil.crop((x, y, x + w, y + h))
                target_image = cv2.cvtColor(np.array(cropped), cv2.COLOR_RGB2BGR)
            elif screenshot_data:
                # 使用整个截图
                img_pil = PILImage.open(io.BytesIO(screenshot_data))
                target_image = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
            else:
                self.logger.warning("未提供有效的图像数据")
                return None
            
            # 图像预处理
            processed_image = self._preprocess_for_ocr(target_image)
            if processed_image is None:
                self.logger.warning("图像预处理失败")
                return None
            # 对于灰度图像，需要指定模式
            if len(processed_image.shape) == 2:
                pil_image = PILImage.fromarray(processed_image, mode='L')
            else:
                pil_image = PILImage.fromarray(processed_image)
            
            # 执行OCR识别
            text = pytesseract.image_to_string(pil_image, config=self.ocr_config)
            cleaned_text = text.strip().replace('\n', ' ').replace('\r', '')
            
            if cleaned_text:
                self.logger.debug(f"OCR识别结果: {cleaned_text}")
                return cleaned_text
            return None
                
        except Exception as e:
            self.logger.error(f"OCR识别错误: {e}")
            return None
    
    def _preprocess_for_ocr(self, image: np.ndarray) -> Optional[np.ndarray]:
        """为OCR预处理图像.
        
        Args:
            image: 输入图像
            
        Returns:
            Optional[np.ndarray]: 预处理后的图像，失败返回None
        """
        try:
            if image is None:
                return None
                
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 图像尺寸检查和调整
            height, width = gray.shape
            if height < 32 or width < 32:
                # 对于过小的图像，进行放大
                scale_factor = max(2.0, 64.0 / min(height, width))
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # 对比度增强 - CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # 双边滤波去噪（保持边缘）
            denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
            
            # 锐化处理
            kernel_sharpen = np.array([[-1, -1, -1],
                                     [-1,  9, -1],
                                     [-1, -1, -1]])
            sharpened = cv2.filter2D(denoised, -1, kernel_sharpen)
            
            # 自适应阈值二值化 - 使用多种方法并选择最佳结果
            # 方法1: 高斯自适应阈值
            binary1 = cv2.adaptiveThreshold(
                sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # 方法2: 均值自适应阈值
            binary2 = cv2.adaptiveThreshold(
                sharpened, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # 方法3: Otsu阈值
            _, binary3 = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 选择最佳二值化结果（基于文本区域的连通性）
            binary = self._select_best_binary(binary1, binary2, binary3)
            
            # 形态学操作优化
            # 去除小噪点
            kernel_noise = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_noise)
            
            # 连接断开的文字
            kernel_connect = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1))
            connected = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel_connect)
            
            # 最终的噪点清理
            kernel_final = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
            final = cv2.morphologyEx(connected, cv2.MORPH_CLOSE, kernel_final)
            
            return final
        except Exception as e:
            self.logger.error(f"图像预处理错误: {e}")
            return None
    
    def _select_best_binary(self, binary1: np.ndarray, binary2: np.ndarray, binary3: np.ndarray) -> np.ndarray:
        """选择最佳的二值化结果.
        
        Args:
            binary1: 高斯自适应阈值结果
            binary2: 均值自适应阈值结果
            binary3: Otsu阈值结果
            
        Returns:
            np.ndarray: 最佳二值化结果
        """
        try:
            # 计算每种方法的文本区域质量指标
            scores = []
            binaries = [binary1, binary2, binary3]
            
            for binary in binaries:
                # 计算连通组件
                num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
                
                # 过滤掉背景和过小/过大的组件
                valid_components = 0
                total_area = 0
                
                for i in range(1, num_labels):  # 跳过背景(0)
                    area = stats[i, cv2.CC_STAT_AREA]
                    width = stats[i, cv2.CC_STAT_WIDTH]
                    height = stats[i, cv2.CC_STAT_HEIGHT]
                    
                    # 文本组件的合理尺寸范围
                    if (10 <= area <= 5000 and 
                        3 <= width <= 200 and 
                        8 <= height <= 100 and
                        0.1 <= width/height <= 10):  # 宽高比合理
                        valid_components += 1
                        total_area += area
                
                # 计算质量分数（有效组件数量和平均面积的平衡）
                if valid_components > 0:
                    avg_area = total_area / valid_components
                    score = valid_components * 0.7 + min(avg_area / 100, 10) * 0.3
                else:
                    score = 0
                
                scores.append(score)
            
            # 选择得分最高的二值化结果
            best_idx = np.argmax(scores)
            return binaries[best_idx]
            
        except Exception as e:
            self.logger.warning(f"二值化选择错误，使用默认方法: {e}")
            return binary1  # 默认返回高斯自适应阈值结果
    
    def find_text(self, target_text: str, screenshot_data: bytes,
                 region: Optional[Tuple[int, int, int, int]] = None) -> Optional[Dict[str, Any]]:
        """在屏幕中查找指定文本.
        
        Args:
            target_text: 要查找的文本
            screenshot_data: 截图数据
            region: 搜索区域 (x, y, width, height)
            
        Returns:
            Optional[Dict[str, Any]]: 找到的文本位置信息
        """
        if not self.enable_ocr or not pytesseract:
            self.logger.warning("OCR功能未启用")
            return None
            
        try:
            img_pil = PILImage.open(io.BytesIO(screenshot_data))
            
            if region:
                x, y, w, h = region
                img_pil = img_pil.crop((x, y, x + w, y + h))
                offset_x, offset_y = x, y
            else:
                offset_x, offset_y = 0, 0
                
            image = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
            processed_image = self._preprocess_for_ocr(image)
            if processed_image is None:
                return None
            # 对于灰度图像，需要指定模式
            if len(processed_image.shape) == 2:
                pil_processed = PILImage.fromarray(processed_image, mode='L')
            else:
                pil_processed = PILImage.fromarray(processed_image)
            
            # 获取文本框位置信息
            data = pytesseract.image_to_data(pil_processed, output_type=pytesseract.Output.DICT)
            
            # 查找目标文本
            for i, text in enumerate(data['text']):
                if text.strip() and target_text.lower() in text.lower():
                    x = data['left'][i] + offset_x
                    y = data['top'][i] + offset_y
                    w = data['width'][i]
                    h = data['height'][i]
                    confidence = float(data['conf'][i]) / 100.0
                    
                    if confidence > 0.5:
                        result = {
                            'text': text.strip(),
                            'position': (x, y),
                            'size': (w, h),
                            'center': (x + w // 2, y + h // 2),
                            'confidence': confidence
                        }
                        self.logger.debug(f"找到文本 '{target_text}': {result}")
                        return result
            
            return None
        except Exception as e:
            self.logger.error(f"文本查找错误: {e}")
            return None
    
    def extract_all_text(self, screenshot_data: bytes,
                        region: Optional[Tuple[int, int, int, int]] = None) -> List[Dict[str, Any]]:
        """提取图像中的所有文本.
        
        Args:
            screenshot_data: 截图数据
            region: 搜索区域 (x, y, width, height)
            
        Returns:
            List[Dict[str, Any]]: 所有文本信息列表
        """
        if not self.enable_ocr or not pytesseract:
            self.logger.warning("OCR功能未启用")
            return []
            
        try:
            img_pil = PILImage.open(io.BytesIO(screenshot_data))
            
            if region:
                x, y, w, h = region
                img_pil = img_pil.crop((x, y, x + w, y + h))
                offset_x, offset_y = x, y
            else:
                offset_x, offset_y = 0, 0
                
            image = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
            processed_image = self._preprocess_for_ocr(image)
            if processed_image is None:
                return []
            # 对于灰度图像，需要指定模式
            if len(processed_image.shape) == 2:
                pil_processed = PILImage.fromarray(processed_image, mode='L')
            else:
                pil_processed = PILImage.fromarray(processed_image)
            
            # 获取所有文本框位置信息
            data = pytesseract.image_to_data(pil_processed, output_type=pytesseract.Output.DICT)
            
            text_list = []
            for i, text in enumerate(data['text']):
                if text.strip():
                    x = data['left'][i] + offset_x
                    y = data['top'][i] + offset_y
                    w = data['width'][i]
                    h = data['height'][i]
                    confidence = float(data['conf'][i]) / 100.0
                    
                    if confidence > 0.3:  # 较低的置信度阈值
                        text_info = {
                            'text': text.strip(),
                            'position': (x, y),
                            'size': (w, h),
                            'center': (x + w // 2, y + h // 2),
                            'confidence': confidence
                        }
                        text_list.append(text_info)
            
            self.logger.debug(f"提取到 {len(text_list)} 个文本")
            return text_list
            
        except Exception as e:
            self.logger.error(f"文本提取错误: {e}")
            return []