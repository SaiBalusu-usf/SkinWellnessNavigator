from flask import Flask, request, jsonify, render_template
import pandas as pd
import numpy as np
from PIL import Image
import io
import os
import signal
import time
from datetime import datetime
import logging
import google.generativeai as genai
from dotenv import load_dotenv
import json
from utils import simulate_gemini_response, SystemMonitor
from logging_config import log_error, log_performance_metrics

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load configuration
class Config:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    CLINICAL_DATA_PATH = 'clinical.csv'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config.from_object(Config)

# Initialize Gemini model
try:
    if not app.config['GEMINI_API_KEY']:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    genai.configure(api_key=app.config['GEMINI_API_KEY'])
    vision_model = genai.GenerativeModel('gemini-pro-vision')
    logger.info("Gemini model initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini model: {e}")
    vision_model = None

# Load clinical data
try:
    clinical_data = pd.read_csv(app.config['CLINICAL_DATA_PATH'])
    logger.info("Clinical data loaded successfully")
except Exception as e:
    logger.error(f"Failed to load clinical data: {e}")
    clinical_data = None

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def preprocess_image(image_data):
    """Preprocess the uploaded image for analysis."""
    try:
        # Convert bytes to image
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize to standard size
        image = image.resize((299, 299))
        
        # Convert to array and normalize
        img_array = np.array(image) / 255.0
        
        return image, img_array
    except Exception as e:
        logger.error(f"Error preprocessing image: {e}")
        raise

def get_clinical_insights(prediction):
    """Get relevant clinical insights based on the prediction."""
    try:
        if clinical_data is None:
            return {}
        
        # Get stage distribution
        stage_distribution = clinical_data['diagnoses_ajcc_pathologic_stage'].value_counts().to_dict()
        
        # Get common morphology
        common_morphology = clinical_data['diagnoses_morphology'].value_counts().index[0]
        
        # Get similar cases count
        similar_cases = len(clinical_data[
            clinical_data['diagnoses_morphology'] == common_morphology
        ])
        
        return {
            'stage_distribution': stage_distribution,
            'common_morphology': common_morphology,
            'similar_cases': similar_cases
        }
    except Exception as e:
        logger.error(f"Error getting clinical insights: {e}")
        return {}

def analyze_with_gemini(image_bytes, mime_type, timeout=15):
    """
    Analyze image using Gemini vision model with timeout handling.
    
    Args:
        image_bytes: Raw image bytes
        mime_type: MIME type of the image
        timeout: Timeout in seconds (default: 15)
        
    Returns:
        dict: Analysis result or fallback result if timeout
    """
    start_time = time.time()
    
    # Define signal handler for timeout
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Gemini model analysis timed out after {timeout} seconds")
    
    try:
        if vision_model is None:
            logger.warning("Gemini model not initialized, using fallback")
            return simulate_gemini_response(mime_type)

        # Set timeout alarm
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        # Prepare image for Gemini
        image_part = {
            "mime_type": mime_type,
            "data": image_bytes
        }

        # Define the prompt
        prompt = """
        Analyze this skin lesion image and provide a detailed assessment in JSON format:
        {
            "classification": "Benign or Malignant",
            "confidence": "0.0 to 1.0",
            "characteristics": {
                "color": "description",
                "border": "description",
                "symmetry": "description",
                "texture": "description"
            },
            "reasoning": "detailed explanation",
            "recommendations": ["list", "of", "recommendations"]
        }
        Focus on ABCDE criteria (Asymmetry, Border, Color, Diameter, Evolution).
        """

        # Generate response
        response = vision_model.generate_content([prompt, image_part])
        response.resolve()

        # Cancel the alarm
        signal.alarm(0)

        # Parse JSON from response
        # Find JSON content between curly braces
        json_str = response.text[response.text.find('{'):response.text.rfind('}')+1]
        analysis_result = json.loads(json_str)
        
        # Log performance metrics
        end_time = time.time()
        log_performance_metrics(logger, start_time, end_time, "Gemini Analysis")
        
        return analysis_result

    except TimeoutError as e:
        # Cancel the alarm to prevent it from firing later
        signal.alarm(0)
        logger.warning(f"Gemini analysis timeout: {str(e)}")
        # Use fallback system
        return simulate_gemini_response(mime_type)
        
    except Exception as e:
        # Cancel the alarm to prevent it from firing later
        signal.alarm(0)
        logger.error(f"Error analyzing with Gemini: {str(e)}")
        # Use fallback system
        return simulate_gemini_response(mime_type)

@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Handle image upload and analysis."""
    start_time = time.time()
    try:
        # Check system health before proceeding
        health_status, health_message = SystemMonitor.check_system_health()
        if not health_status:
            logger.warning(f"System health check failed: {health_message}")
            return jsonify({
                'error': 'System is currently under heavy load',
                'details': health_message,
                'retry_after': 30  # Suggest retrying after 30 seconds
            }), 503  # Service Unavailable
        
        # Check if image was uploaded
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        # Validate file
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Read and preprocess image
        image_bytes = file.read()
        
        # Additional security check - verify it's a valid image
        try:
            image, processed_array = preprocess_image(image_bytes)
        except Exception as e:
            logger.warning(f"Invalid image content in file {file.filename}: {str(e)}")
            return jsonify({'error': 'Invalid image content'}), 400
        
        # Get AI analysis
        analysis_result = analyze_with_gemini(image_bytes, file.mimetype)
        
        # Check if we got a fallback result
        using_fallback = 'is_fallback' in analysis_result and analysis_result['is_fallback']
        
        # Get clinical insights
        clinical_insights = get_clinical_insights(analysis_result['classification'])
        
        # Combine results
        results = {
            'prediction': analysis_result['classification'],
            'confidence': analysis_result['confidence'],
            'characteristics': analysis_result['characteristics'],
            'reasoning': analysis_result['reasoning'],
            'recommendations': analysis_result['recommendations'],
            'clinical_insights': clinical_insights,
            'timestamp': datetime.now().isoformat(),
            'using_fallback': using_fallback  # Let the frontend know if we used the fallback
        }
        
        # Log performance for the entire request
        end_time = time.time()
        log_performance_metrics(logger, start_time, end_time, f"API Analysis Request - {'Fallback' if using_fallback else 'Normal'}")
        
        status_message = "Analysis completed successfully"
        if using_fallback:
            status_message += " (using fallback mechanism)"
        logger.info(f"{status_message} for file: {file.filename}")
        
        return jsonify(results)
    
    except Exception as e:
        log_error(logger, e, f"Error processing analysis request for file: {file.filename if 'file' in locals() else 'unknown'}")
        return jsonify({
            'error': 'An error occurred during analysis',
            'details': str(e)
        }), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({'error': 'File is too large'}), 413

@app.errorhandler(500)
def server_error(e):
    """Handle internal server error."""
    logger.error(f"Internal server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
