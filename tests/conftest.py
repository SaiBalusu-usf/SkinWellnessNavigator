"""
Pytest configuration and fixtures for the Skin Wellness Navigator test suite.
"""

import os
import pytest
import tempfile
import shutil
from PIL import Image
import numpy as np
import json
from datetime import datetime
from typing import Dict, Any

from server import app
from utils import ImageProcessor, ClinicalDataProcessor
from config import TestingConfig

@pytest.fixture(scope='session')
def test_app():
    """Create a test application instance."""
    app.config.from_object(TestingConfig)
    return app

@pytest.fixture(scope='session')
def test_client(test_app):
    """Create a test client."""
    return test_app.test_client()

@pytest.fixture(scope='function')
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture(scope='function')
def test_image():
    """Create a test image."""
    image = Image.new('RGB', (100, 100), color='white')
    # Add some features to make it more realistic
    pixels = image.load()
    for i in range(40, 60):
        for j in range(40, 60):
            pixels[i, j] = (100, 150, 200)
    return image

@pytest.fixture(scope='function')
def test_image_file(test_image, temp_dir):
    """Save test image to a temporary file."""
    filepath = os.path.join(temp_dir, 'test_image.png')
    test_image.save(filepath)
    return filepath

@pytest.fixture(scope='session')
def test_clinical_data():
    """Create test clinical data."""
    return {
        'cases_submitter_id': ['TCGA-01', 'TCGA-02', 'TCGA-03'],
        'demographic_gender': ['male', 'female', 'male'],
        'demographic_age_at_index': [45, 52, 38],
        'demographic_vital_status': ['Alive', 'Deceased', 'Alive'],
        'demographic_race': ['white', 'black', 'asian'],
        'cases_primary_site': ['Skin', 'Skin', 'Skin'],
        'cases_disease_type': ['Melanoma', 'Melanoma', 'Melanoma'],
        'diagnoses_ajcc_pathologic_stage': ['Stage I', 'Stage II', 'Stage I'],
        'diagnoses_morphology': ['8720/3', '8721/3', '8720/3'],
        'treatments_treatment_type': ['Surgery', 'Radiation', 'Surgery'],
        'treatments_treatment_outcome': ['Complete Response', 'Partial Response', 'Complete Response'],
        'treatments_treatment_intent_type': ['Curative', 'Curative', 'Palliative']
    }

@pytest.fixture(scope='session')
def mock_gemini_response():
    """Create mock Gemini API response."""
    return {
        'classification': 'benign',
        'confidence': 0.85,
        'characteristics': {
            'color': 'uniform brown',
            'border': 'well-defined',
            'symmetry': 'symmetric',
            'texture': 'smooth'
        },
        'reasoning': 'The lesion shows regular borders, uniform coloring, and symmetrical shape...',
        'recommendations': [
            'Continue regular self-examinations',
            'Use sun protection daily',
            'Schedule follow-up in 6 months'
        ]
    }

@pytest.fixture(scope='function')
def mock_analysis_result():
    """Create mock analysis result."""
    return {
        'prediction': 'benign',
        'confidence': 0.85,
        'timestamp': datetime.now().isoformat(),
        'clinical_statistics': {
            'stage_distribution': {'Stage I': 2, 'Stage II': 1},
            'similar_cases': 15
        },
        'characteristics': {
            'color': 'uniform brown',
            'border': 'well-defined',
            'symmetry': 'symmetric',
            'texture': 'smooth'
        },
        'recommendations': [
            'Continue regular self-examinations',
            'Use sun protection daily',
            'Schedule follow-up in 6 months'
        ]
    }

class MockResponse:
    """Mock HTTP response."""
    def __init__(self, json_data: Dict[str, Any], status_code: int = 200):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")

@pytest.fixture(scope='function')
def mock_successful_response(mock_analysis_result):
    """Create successful mock response."""
    return MockResponse(mock_analysis_result)

@pytest.fixture(scope='function')
def mock_error_response():
    """Create error mock response."""
    return MockResponse(
        {'error': 'Analysis failed', 'message': 'Invalid image format'},
        status_code=400
    )

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "api: marks tests as API tests")

def pytest_collection_modifyitems(config, items):
    """Modify test items in-place to handle markers."""
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

@pytest.fixture(scope='session')
def image_processor():
    """Create image processor instance."""
    return ImageProcessor()

@pytest.fixture(scope='session')
def clinical_processor(test_clinical_data, temp_dir):
    """Create clinical data processor instance."""
    # Create temporary CSV file
    csv_path = os.path.join(temp_dir, 'test_clinical.csv')
    import pandas as pd
    pd.DataFrame(test_clinical_data).to_csv(csv_path, index=False)
    return ClinicalDataProcessor(csv_path)

def pytest_assertrepr_compare(op, left, right):
    """Custom assertion explanations."""
    if isinstance(left, np.ndarray) and isinstance(right, np.ndarray) and op == "==":
        return [
            "Array comparison failed:",
            f"Shape: {left.shape} != {right.shape}",
            f"Max difference: {np.max(np.abs(left - right))}",
            f"Mean difference: {np.mean(np.abs(left - right))}"
        ]
