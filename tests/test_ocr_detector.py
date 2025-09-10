"""OCR检测器测试模块.

测试OCR文本识别功能。"""

import pytest
import cv2
import numpy as np
import io
from unittest.mock import Mock, patch, MagicMock
from PIL import Image as PILImage

from src.core.ocr_detector import OCRDetector


class TestOCRDetector:
    """OCR检测器测试类."""

    def setup_method(self):
        """设置测试环境."""
        self.ocr_detector = OCRDetector()
        # 创建测试图像 - 确保是正确的numpy数组格式
        self.test_image = np.ones((100, 200, 3), dtype=np.uint8) * 255  # 白色背景
        # 创建测试截图数据
        test_pil = PILImage.fromarray(self.test_image)
        buffer = io.BytesIO()
        test_pil.save(buffer, format='PNG')
        self.test_screenshot_data = buffer.getvalue()

    def test_init(self):
        """测试初始化."""
        detector = OCRDetector()
        assert detector.enable_ocr is True
        assert detector.ocr_config is not None
        assert detector.logger is not None

    def test_preprocess_for_ocr(self):
        """测试图像预处理."""
        # 测试彩色图像预处理
        processed = self.ocr_detector._preprocess_for_ocr(self.test_image)
        assert processed is not None
        assert len(processed.shape) == 2  # 应该是灰度图
        
        # 测试灰度图像预处理
        gray_image = cv2.cvtColor(self.test_image, cv2.COLOR_BGR2GRAY)
        processed_gray = self.ocr_detector._preprocess_for_ocr(gray_image)
        assert processed_gray is not None
        assert len(processed_gray.shape) == 2

    @patch('src.core.ocr_detector.pytesseract')
    @patch('src.core.ocr_detector.PILImage')
    def test_recognize_text_with_image_region(self, mock_pil, mock_pytesseract):
        """测试使用图像区域进行文本识别."""
        mock_pytesseract.image_to_string.return_value = "Test Text"
        
        # 模拟PIL图像
        mock_img = Mock()
        mock_pil.open.return_value = mock_img
        
        # 模拟numpy数组转换和预处理
        with patch('numpy.array', return_value=self.test_image), patch('cv2.cvtColor', return_value=self.test_image):
            with patch.object(self.ocr_detector, '_preprocess_for_ocr', return_value=np.zeros((50, 100), dtype=np.uint8)):
                result = self.ocr_detector.recognize_text(screenshot_data=self.test_screenshot_data)
                
                assert result == "Test Text"
                mock_pytesseract.image_to_string.assert_called_once()

    @patch('src.core.ocr_detector.pytesseract')
    @patch('src.core.ocr_detector.PILImage')
    def test_recognize_text_with_screenshot_and_region(self, mock_pil, mock_pytesseract):
        """测试使用截图数据和区域进行文本识别."""
        # 模拟PIL图像
        mock_img = Mock()
        mock_cropped = Mock()
        mock_img.crop.return_value = mock_cropped
        mock_pil.open.return_value = mock_img
        
        # 模拟numpy数组转换
        mock_array = np.zeros((50, 100, 3), dtype=np.uint8)
        with patch('numpy.array', return_value=mock_array):
            mock_pytesseract.image_to_string.return_value = "Cropped Text"
            
            result = self.ocr_detector.recognize_text(
                screenshot_data=self.test_screenshot_data,
                region=(10, 10, 50, 30)
            )
            
            assert result == "Cropped Text"
            mock_img.crop.assert_called_once_with((10, 10, 60, 40))

    def test_recognize_text_ocr_disabled(self):
        """测试OCR功能禁用时的行为."""
        self.ocr_detector.enable_ocr = False
        
        result = self.ocr_detector.recognize_text(image_region=self.test_image)
        
        assert result is None

    @patch('src.core.ocr_detector.pytesseract', None)
    def test_recognize_text_pytesseract_not_available(self):
        """测试pytesseract不可用时的行为."""
        detector = OCRDetector()
        
        result = detector.recognize_text(image_region=self.test_image)
        
        assert result is None

    @patch('src.core.ocr_detector.pytesseract')
    @patch('src.core.ocr_detector.PILImage')
    def test_find_text(self, mock_pil, mock_pytesseract):
        """测试文本查找功能."""
        # 模拟PIL图像
        mock_img = Mock()
        mock_pil.open.return_value = mock_img
        
        # 模拟OCR数据输出
        mock_data = {
            'text': ['', 'Hello', 'World', 'Test'],
            'left': [0, 10, 50, 90],
            'top': [0, 20, 25, 30],
            'width': [0, 30, 35, 40],
            'height': [0, 15, 18, 20],
            'conf': [0, 85, 90, 95]
        }
        mock_pytesseract.image_to_data.return_value = mock_data
        mock_pytesseract.Output.DICT = 'dict'
        
        with patch('numpy.array', return_value=self.test_image), patch('cv2.cvtColor', return_value=self.test_image):
            with patch.object(self.ocr_detector, '_preprocess_for_ocr', return_value=np.zeros((100, 200), dtype=np.uint8)):
                result = self.ocr_detector.find_text("hello", self.test_screenshot_data)
            
            assert result is not None
            assert result['text'] == 'Hello'
            assert result['position'] == (10, 20)
            assert result['size'] == (30, 15)
            assert result['center'] == (25, 27)
            assert result['confidence'] == 0.85

    @patch('src.core.ocr_detector.pytesseract')
    @patch('src.core.ocr_detector.PILImage')
    def test_find_text_with_region(self, mock_pil, mock_pytesseract):
        """测试在指定区域查找文本."""
        # 模拟PIL图像
        mock_img = Mock()
        mock_cropped = Mock()
        mock_img.crop.return_value = mock_cropped
        mock_pil.open.return_value = mock_img
        
        # 模拟OCR数据输出
        mock_data = {
            'text': ['Target'],
            'left': [5],
            'top': [10],
            'width': [25],
            'height': [12],
            'conf': [88]
        }
        mock_pytesseract.image_to_data.return_value = mock_data
        mock_pytesseract.Output.DICT = 'dict'
        
        with patch('numpy.array', return_value=self.test_image), patch('cv2.cvtColor', return_value=self.test_image):
            with patch.object(self.ocr_detector, '_preprocess_for_ocr', return_value=np.zeros((100, 200), dtype=np.uint8)):
                result = self.ocr_detector.find_text(
                    "target", 
                    self.test_screenshot_data, 
                    region=(100, 50, 200, 100)
                )
            
            assert result is not None
            assert result['position'] == (105, 60)  # 5+100, 10+50
            mock_img.crop.assert_called_once_with((100, 50, 300, 150))

    @patch('src.core.ocr_detector.pytesseract')
    @patch('src.core.ocr_detector.PILImage')
    def test_extract_all_text(self, mock_pil, mock_pytesseract):
        """测试提取所有文本功能."""
        # 模拟PIL图像
        mock_img = Mock()
        mock_pil.open.return_value = mock_img
        
        # 模拟OCR数据输出
        mock_data = {
            'text': ['', 'First', 'Second', 'Third'],
            'left': [0, 10, 50, 90],
            'top': [0, 20, 25, 30],
            'width': [0, 30, 35, 40],
            'height': [0, 15, 18, 20],
            'conf': [0, 85, 25, 95]  # Second的置信度较低(25 < 30)
        }
        mock_pytesseract.image_to_data.return_value = mock_data
        mock_pytesseract.Output.DICT = 'dict'
        
        with patch('numpy.array', return_value=self.test_image), patch('cv2.cvtColor', return_value=self.test_image):
            with patch.object(self.ocr_detector, '_preprocess_for_ocr', return_value=np.zeros((100, 200), dtype=np.uint8)):
                result = self.ocr_detector.extract_all_text(self.test_screenshot_data)
            
            assert len(result) == 2  # 只有置信度>0.3的文本
            assert result[0]['text'] == 'First'
            assert result[1]['text'] == 'Third'

    def test_extract_all_text_ocr_disabled(self):
        """测试OCR禁用时提取所有文本的行为."""
        self.ocr_detector.enable_ocr = False
        
        result = self.ocr_detector.extract_all_text(self.test_screenshot_data)
        
        assert result == []

    @patch('src.core.ocr_detector.pytesseract')
    def test_recognize_text_exception_handling(self, mock_pytesseract):
        """测试异常处理."""
        mock_pytesseract.image_to_string.side_effect = Exception("OCR Error")
        
        result = self.ocr_detector.recognize_text(image_region=self.test_image)
        
        assert result is None

    def test_preprocess_for_ocr_exception_handling(self):
        """测试图像预处理异常处理."""
        # 传入无效图像
        invalid_image = None
        
        result = self.ocr_detector._preprocess_for_ocr(invalid_image)
        
        assert result is None

    def test_recognize_text_no_input(self):
        """测试没有输入时的行为."""
        result = self.ocr_detector.recognize_text()
        
        assert result is None

    @patch('src.core.ocr_detector.pytesseract')
    def test_recognize_text_empty_result(self, mock_pytesseract):
        """测试OCR返回空结果的情况."""
        mock_pytesseract.image_to_string.return_value = "   \n\r  "
        
        result = self.ocr_detector.recognize_text(image_region=self.test_image)
        
        assert result is None

    @patch('src.core.ocr_detector.pytesseract')
    @patch('src.core.ocr_detector.PILImage')
    def test_find_text_no_match(self, mock_pil, mock_pytesseract):
        """测试找不到目标文本的情况."""
        # 模拟PIL图像
        mock_img = Mock()
        mock_pil.open.return_value = mock_img
        
        # 模拟OCR数据输出（没有匹配的文本）
        mock_data = {
            'text': ['Hello', 'World'],
            'left': [10, 50],
            'top': [20, 25],
            'width': [30, 35],
            'height': [15, 18],
            'conf': [85, 90]
        }
        mock_pytesseract.image_to_data.return_value = mock_data
        mock_pytesseract.Output.DICT = 'dict'
        
        with patch('numpy.array'), patch('cv2.cvtColor'):
            result = self.ocr_detector.find_text("NotFound", self.test_screenshot_data)
            
            assert result is None

    @patch('src.core.ocr_detector.pytesseract')
    @patch('src.core.ocr_detector.PILImage')
    def test_find_text_low_confidence(self, mock_pil, mock_pytesseract):
        """测试低置信度文本的处理."""
        # 模拟PIL图像
        mock_img = Mock()
        mock_pil.open.return_value = mock_img
        
        # 模拟OCR数据输出（低置信度）
        mock_data = {
            'text': ['Target'],
            'left': [10],
            'top': [20],
            'width': [30],
            'height': [15],
            'conf': [30]  # 低置信度
        }
        mock_pytesseract.image_to_data.return_value = mock_data
        mock_pytesseract.Output.DICT = 'dict'
        
        with patch('numpy.array'), patch('cv2.cvtColor'):
            result = self.ocr_detector.find_text("target", self.test_screenshot_data)
            
            assert result is None  # 置信度太低，应该返回None