"""Failure-path tests using synthetic images and mocked model calls."""

import io
import json
from unittest.mock import patch

from PIL import Image

import server
from utils import analysis_unavailable_result


def synthetic_image():
    image = Image.new('RGB', (2, 2), color=(255, 255, 255))
    data = io.BytesIO()
    image.save(data, format='PNG')
    data.seek(0)
    return data


def test_unavailable_result_has_no_diagnostic_fields():
    result = analysis_unavailable_result()
    assert result['status'] == 'analysis_unavailable'
    assert 'classification' not in result
    assert 'confidence' not in result


def test_missing_model_returns_unavailable():
    with patch.object(server, 'vision_model', None):
        result = server.analyze_with_gemini(b'synthetic', 'image/png')
    assert result == analysis_unavailable_result()


def test_model_exception_returns_unavailable():
    class FailingModel:
        def generate_content(self, *args, **kwargs):
            raise RuntimeError('synthetic service failure')

    with patch.object(server, 'vision_model', FailingModel()):
        result = server.analyze_with_gemini(b'synthetic', 'image/png')
    assert result == analysis_unavailable_result()


def test_api_returns_503_without_diagnostic_fields():
    with patch.object(server.SystemMonitor, 'check_system_health', return_value=(True, 'ok')):
        with patch.object(server, 'vision_model', None):
            response = server.app.test_client().post(
                '/api/analyze',
                data={'image': (synthetic_image(), 'synthetic.png')},
                content_type='multipart/form-data',
            )
    result = response.get_json()
    assert response.status_code == 503
    assert result['status'] == 'analysis_unavailable'
    assert 'prediction' not in result
    assert 'confidence' not in result
    assert 'clinical_insights' not in result
