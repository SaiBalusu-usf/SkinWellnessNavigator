"""
Test utilities and helper functions for the Skin Wellness Navigator test suite.
"""

import os
import pytest
import numpy as np
from PIL import Image
import io
import json
from datetime import datetime
from typing import Dict, Any, Tuple, BinaryIO
import base64

class TestDataGenerator:
    """Generate test data for various test scenarios."""
    
    @staticmethod
    def create_test_image(
        size: Tuple[int, int] = (100, 100),
        color: Tuple[int, int, int] = (255, 255, 255),
        format: str = 'PNG'
    ) -> BinaryIO:
        """
        Create a test image with specified parameters.
        
        Args:
            size: Image dimensions (width, height)
            color: RGB color tuple
            format: Image format (PNG, JPEG, etc.)
            
        Returns:
            BytesIO object containing the image
        """
        img = Image.new('RGB', size, color=color)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format=format)
        img_byte_arr.seek(0)
        return img_byte_arr

    @staticmethod
    def create_test_clinical_data() -> Dict[str, Any]:
        """
        Create mock clinical data for testing.
        
        Returns:
            Dictionary containing mock clinical data
        """
        return {
            'demographic_age_at_index': [45, 52, 38, 61],
            'demographic_gender': ['M', 'F', 'M', 'F'],
            'diagnoses_ajcc_pathologic_stage': ['Stage I', 'Stage II', 'Stage I', 'Stage III'],
            'diagnoses_morphology': ['type_1', 'type_2', 'type_1', 'type_3'],
            'treatments_treatment_type': ['Surgery', 'Radiation', 'Surgery', 'Chemotherapy'],
            'treatments_treatment_outcome': ['Complete Response', 'Partial Response', 
                                          'Complete Response', 'Stable Disease']
        }

    @staticmethod
    def create_test_analysis_result() -> Dict[str, Any]:
        """
        Create mock analysis result for testing.
        
        Returns:
            Dictionary containing mock analysis result
        """
        return {
            'prediction': 'benign',
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat(),
            'characteristics': {
                'color': 'uniform',
                'border': 'regular',
                'symmetry': 'symmetric',
                'texture': 'smooth'
            },
            'recommendations': [
                'Continue regular monitoring',
                'Use sun protection',
                'Schedule routine check-up'
            ]
        }

class MockResponse:
    """Mock HTTP response for testing API calls."""
    
    def __init__(self, status_code: int, json_data: Dict[str, Any]):
        self.status_code = status_code
        self._json_data = json_data
        self.text = json.dumps(json_data)

    def json(self) -> Dict[str, Any]:
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")

@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response."""
    return {
        'classification': 'benign',
        'confidence': 0.85,
        'characteristics': {
            'color': 'uniform',
            'border': 'regular',
            'symmetry': 'symmetric',
            'texture': 'smooth'
        },
        'reasoning': 'The lesion shows regular borders and uniform coloring...',
        'recommendations': [
            'Continue regular monitoring',
            'Use sun protection',
            'Schedule routine check-up'
        ]
    }

@pytest.fixture
def mock_clinical_data():
    """Mock clinical dataset."""
    return TestDataGenerator.create_test_clinical_data()

@pytest.fixture
def mock_analysis_result():
    """Mock analysis result."""
    return TestDataGenerator.create_test_analysis_result()

@pytest.fixture
def test_image():
    """Generate test image."""
    return TestDataGenerator.create_test_image()

def assert_valid_image_array(arr: np.ndarray):
    """
    Assert that an array is a valid image array.
    
    Args:
        arr: NumPy array to validate
    """
    assert isinstance(arr, np.ndarray)
    assert len(arr.shape) == 3  # Height, width, channels
    assert arr.shape[2] == 3    # RGB channels
    assert arr.dtype == np.float32 or arr.dtype == np.float64
    assert np.all(arr >= 0) and np.all(arr <= 1)  # Normalized values

def assert_valid_prediction_result(result: Dict[str, Any]):
    """
    Assert that a prediction result has all required fields.
    
    Args:
        result: Prediction result dictionary to validate
    """
    required_fields = {
        'prediction': str,
        'confidence': float,
        'timestamp': str,
        'characteristics': dict,
        'recommendations': list
    }
    
    for field, field_type in required_fields.items():
        assert field in result
        assert isinstance(result[field], field_type)
    
    assert 0 <= result['confidence'] <= 1
    assert len(result['recommendations']) > 0

def create_mock_file(content: bytes, filename: str) -> Any:
    """
    Create a mock file object for testing file uploads.
    
    Args:
        content: File content as bytes
        filename: Name of the file
        
    Returns:
        Mock file object
    """
    class MockFile:
        def __init__(self, content, filename):
            self.content = content
            self.filename = filename
            self._position = 0

        def read(self):
            return self.content

        def seek(self, position):
            self._position = position

    return MockFile(content, filename)

def encode_image_base64(image_path: str) -> str:
    """
    Encode an image file as base64.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 encoded string
    """
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def create_test_directory_structure(base_path: str):
    """
    Create a test directory structure.
    
    Args:
        base_path: Base path for the test directory structure
    """
    directories = [
        'uploads',
        'logs',
        'model_cache',
        'static/images',
        'static/css',
        'static/js',
        'templates'
    ]
    
    for directory in directories:
        os.makedirs(os.path.join(base_path, directory), exist_ok=True)

def cleanup_test_files(base_path: str):
    """
    Clean up test files and directories.
    
    Args:
        base_path: Base path for cleanup
    """
    import shutil
    if os.path.exists(base_path):
        shutil.rmtree(base_path)

class MockLogger:
    """Mock logger for testing."""
    
    def __init__(self):
        self.logs = []

    def info(self, message):
        self.logs.append(('INFO', message))

    def error(self, message):
        self.logs.append(('ERROR', message))

    def warning(self, message):
        self.logs.append(('WARNING', message))

    def debug(self, message):
        self.logs.append(('DEBUG', message))

@pytest.fixture
def mock_logger():
    """Provide a mock logger for testing."""
    return MockLogger()

def compare_images(image1: Image.Image, image2: Image.Image, tolerance: float = 0.1) -> bool:
    """
    Compare two images for similarity.
    
    Args:
        image1: First image
        image2: Second image
        tolerance: Tolerance for difference
        
    Returns:
        bool: True if images are similar within tolerance
    """
    # Convert images to arrays
    arr1 = np.array(image1)
    arr2 = np.array(image2)
    
    if arr1.shape != arr2.shape:
        return False
    
    # Calculate mean absolute difference
    diff = np.mean(np.abs(arr1 - arr2))
    return diff <= tolerance

class TestEnvironment:
    """Context manager for setting up and tearing down test environment."""
    
    def __init__(self, base_path: str):
        self.base_path = base_path

    def __enter__(self):
        create_test_directory_structure(self.base_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        cleanup_test_files(self.base_path)
