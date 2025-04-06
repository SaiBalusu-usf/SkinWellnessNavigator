import os
import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from PIL import Image
import io
import json
from datetime import datetime

# Import application modules
from server import app
from utils import ImageProcessor, ClinicalDataProcessor, ResultsFormatter, SystemMonitor
from config import TestingConfig, get_config
from logging_config import setup_logging

@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config.from_object(TestingConfig)
    with app.test_client() as client:
        yield client

@pytest.fixture
def sample_image():
    """Create a sample test image."""
    img = Image.new('RGB', (100, 100), color='white')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

@pytest.fixture
def mock_clinical_data():
    """Create mock clinical data."""
    return {
        'stage_distribution': {'Stage I': 10, 'Stage II': 20},
        'age_distribution': {'mean': 50.0, 'median': 48.0, 'std': 15.0},
        'gender_distribution': {'M': 30, 'F': 25},
        'similar_cases': 15
    }

class TestConfig:
    """Test configuration settings."""

    def test_config_loading(self):
        """Test configuration loading based on environment."""
        with patch.dict('os.environ', {'FLASK_ENV': 'testing'}):
            config = get_config()
            assert config == TestingConfig
            assert config.TESTING is True
            assert config.DEBUG is True

    def test_environment_variables(self):
        """Test environment variable handling."""
        test_api_key = 'test_key_123'
        with patch.dict('os.environ', {'GEMINI_API_KEY': test_api_key}):
            config = TestingConfig()
            assert config.GEMINI_API_KEY == test_api_key

class TestImageProcessor:
    """Test image processing functionality."""

    def test_validate_image(self):
        """Test image validation."""
        processor = ImageProcessor()
        
        # Test valid image
        mock_file = MagicMock()
        mock_file.filename = 'test.jpg'
        mock_file.read.return_value = b'dummy_data'
        assert processor.validate_image(mock_file) is True
        
        # Test invalid extension
        mock_file.filename = 'test.txt'
        assert processor.validate_image(mock_file) is False

    def test_preprocess_image(self, sample_image):
        """Test image preprocessing."""
        processor = ImageProcessor()
        result = processor.preprocess_image(sample_image.getvalue())
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (299, 299, 3)
        assert np.max(result) <= 1.0
        assert np.min(result) >= 0.0

class TestClinicalDataProcessor:
    """Test clinical data processing."""

    @pytest.fixture
    def mock_csv_data(self):
        """Create mock CSV data."""
        return """demographic_age_at_index,demographic_gender,diagnoses_ajcc_pathologic_stage,diagnoses_morphology
45,M,Stage I,type_1
52,F,Stage II,type_2
"""

    def test_load_data(self, tmp_path, mock_csv_data):
        """Test loading clinical data."""
        # Create temporary CSV file
        csv_file = tmp_path / "test_clinical.csv"
        csv_file.write_text(mock_csv_data)
        
        processor = ClinicalDataProcessor(str(csv_file))
        assert processor.data is not None
        assert len(processor.data) == 2

    def test_get_statistics(self, tmp_path, mock_csv_data):
        """Test statistics calculation."""
        csv_file = tmp_path / "test_clinical.csv"
        csv_file.write_text(mock_csv_data)
        
        processor = ClinicalDataProcessor(str(csv_file))
        stats = processor.get_statistics('type_1')
        
        assert 'stage_distribution' in stats
        assert 'age_distribution' in stats
        assert 'gender_distribution' in stats

class TestResultsFormatter:
    """Test results formatting functionality."""

    def test_format_prediction(self, mock_clinical_data):
        """Test prediction formatting."""
        formatter = ResultsFormatter()
        result = formatter.format_prediction(
            prediction='malignant',
            confidence=0.85,
            clinical_stats=mock_clinical_data,
            characteristics={'color': 'dark', 'border': 'irregular'}
        )
        
        assert 'prediction' in result
        assert 'confidence' in result
        assert 'timestamp' in result
        assert 'recommendations' in result
        assert isinstance(result['confidence'], float)
        assert isinstance(result['timestamp'], str)

    def test_get_recommendations(self):
        """Test recommendation generation."""
        recommendations = ResultsFormatter.get_recommendations('malignant', 0.9)
        assert len(recommendations) > 0
        assert isinstance(recommendations, list)
        assert all(isinstance(rec, str) for rec in recommendations)

class TestSystemMonitor:
    """Test system monitoring functionality."""

    def test_get_system_metrics(self):
        """Test system metrics collection."""
        metrics = SystemMonitor.get_system_metrics()
        assert 'cpu_usage' in metrics
        assert 'memory_usage' in metrics
        assert 'disk_usage' in metrics
        assert all(isinstance(v, (int, float)) for v in metrics.values())

    def test_check_system_health(self):
        """Test system health check."""
        with patch('utils.SystemMonitor.get_system_metrics') as mock_metrics:
            mock_metrics.return_value = {
                'cpu_usage': 50,
                'memory_usage': 60,
                'disk_usage': 70
            }
            status, message = SystemMonitor.check_system_health()
            assert status is True
            assert isinstance(message, str)

class TestAPI:
    """Test API endpoints."""

    def test_home_page(self, client):
        """Test home page loading."""
        response = client.get('/')
        assert response.status_code == 200

    def test_analyze_endpoint(self, client, sample_image):
        """Test image analysis endpoint."""
        data = {
            'image': (sample_image, 'test.png')
        }
        response = client.post('/api/analyze', data=data)
        assert response.status_code in [200, 400, 500]

    def test_error_handling(self, client):
        """Test error handling."""
        response = client.post('/api/analyze')
        assert response.status_code == 400
        assert b'error' in response.data

if __name__ == '__main__':
    pytest.main([__file__])
