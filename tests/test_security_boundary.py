"""Local security regressions; the provider SDK is stubbed, no credentials/network."""
import importlib
import io
import logging
import os
import sys
import types
import unittest
from unittest.mock import patch
from PIL import Image

def image_bytes(fmt='PNG', size=(2, 2)):
    data = io.BytesIO()
    Image.new('RGB', size).save(data, format=fmt)
    return data.getvalue()

class SecurityBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        google = sys.modules.setdefault('google', types.ModuleType('google'))
        sdk = types.ModuleType('google.generativeai')
        google.generativeai = sdk
        sys.modules.setdefault('google.generativeai', sdk)
        with patch.dict(os.environ, {'GEMINI_API_KEY': ''}), patch('dotenv.load_dotenv'), patch('logging.FileHandler', return_value=logging.NullHandler()):
            cls.server = importlib.import_module('server')
        cls.server.app.config['TESTING'] = True

    def post(self, data=None, **kwargs):
        with patch.object(self.server.SystemMonitor, 'check_system_health', return_value=(True, 'ok')):
            return self.server.app.test_client().post('/api/analyze', data={'image': (io.BytesIO(data or image_bytes()), 'synthetic.png')}, **kwargs)

    def test_remote_requests_never_call_provider(self):
        with patch.object(self.server, 'analyze_with_gemini') as provider:
            response = self.post(environ_overrides={'REMOTE_ADDR':'192.0.2.1'})
        self.assertEqual(response.status_code, 403)
        provider.assert_not_called()

    def test_cross_origin_requests_are_rejected(self):
        self.assertEqual(self.post(headers={'Origin':'https://attacker.example'}).status_code, 403)

    def test_only_png_or_jpeg_decodes_are_accepted(self):
        self.assertEqual(self.post(image_bytes('GIF')).status_code, 400)

    def test_pixel_limit_applies_before_image_decode(self):
        with patch.object(self.server.Image, 'open') as opened:
            opened.return_value.__enter__.return_value.size = (100000, 100000)
            opened.return_value.__enter__.return_value.format = 'PNG'
            with self.assertRaises(ValueError):
                self.server.preprocess_image(b'synthetic')

    def test_provider_receives_normalized_png(self):
        unavailable = {'status':'analysis_unavailable'}
        with patch.object(self.server, 'analyze_with_gemini', return_value=unavailable) as provider:
            self.assertEqual(self.post(image_bytes('JPEG')).status_code, 503)
        payload, mime = provider.call_args.args
        self.assertEqual(mime, 'image/png')
        self.assertTrue(payload.startswith(b'\x89PNG\r\n\x1a\n'))

    def test_internal_error_details_are_not_returned(self):
        with patch.object(self.server, 'analyze_with_gemini', side_effect=RuntimeError('private synthetic diagnostic')):
            response=self.post()
        self.assertEqual(response.status_code, 500)
        self.assertNotIn(b'private synthetic diagnostic', response.data)

    def test_oversized_requests_keep_413(self):
        with patch.dict(self.server.app.config, {'MAX_CONTENT_LENGTH':64}):
            self.assertEqual(self.post().status_code,413)

if __name__ == '__main__':
    unittest.main()
