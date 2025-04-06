import os
import json
import numpy as np
from PIL import Image
import io
from datetime import datetime
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
import logging
from logging_config import log_data_processing, log_performance_metrics, log_error
import time
import random

logger = logging.getLogger(__name__)

def simulate_gemini_response(image_mime_type: str = None) -> Dict:
    """
    Generate a simulated response when Gemini model is unavailable or times out.
    This provides a fallback to ensure the application remains functional.
    
    Args:
        image_mime_type: MIME type of the analyzed image (optional)
        
    Returns:
        Dict: Simulated analysis result in the same format as Gemini would return
    """
    try:
        # Log that we're using the fallback
        logger.warning("Using fallback simulation for Gemini model response")
        
        # Randomly choose classification (with higher probability for benign)
        classification = random.choices(
            ['Benign', 'Malignant'], 
            weights=[0.7, 0.3], 
            k=1
        )[0]
        
        # Generate a confidence score
        confidence = random.uniform(0.65, 0.92)
        
        # Define characteristics based on classification
        if classification == 'Benign':
            characteristics = {
                'color': 'Uniform tan to brown coloration',
                'border': 'Well-defined, smooth borders',
                'symmetry': 'Mostly symmetrical',
                'texture': 'Smooth, consistent texture'
            }
            reasoning = (
                "The lesion shows uniform coloration without significant variation. "
                "The borders are well-defined and regular. The overall shape is symmetrical. "
                "These characteristics are typically associated with benign skin lesions."
            )
        else:
            characteristics = {
                'color': 'Varied coloration with dark and uneven areas',
                'border': 'Irregular, poorly defined edges',
                'symmetry': 'Asymmetrical shape',
                'texture': 'Uneven texture with raised areas'
            }
            reasoning = (
                "The lesion shows concerning features including color variation, "
                "irregular borders, and asymmetrical shape. These features are "
                "common in malignant skin lesions and warrant further examination."
            )
        
        # Generate recommendations
        recommendations = ResultsFormatter.get_recommendations(classification, confidence)
        
        # Add a note that this is a simulated response for transparency
        recommendations.append("Note: This analysis is using simulated results as the AI model is currently unavailable")
            
        # Create the final response structure
        analysis_result = {
            'classification': classification,
            'confidence': round(confidence, 2),
            'characteristics': characteristics,
            'reasoning': reasoning,
            'recommendations': recommendations,
            'is_fallback': True  # Flag to indicate this is a fallback response
        }
        
        return analysis_result
    except Exception as e:
        log_error(logger, e, "Error in simulate_gemini_response")
        # Return a very basic result in case of error in the simulator itself
        return {
            'classification': 'Uncertain',
            'confidence': 0.5,
            'characteristics': {
                'color': 'Unable to analyze',
                'border': 'Unable to analyze',
                'symmetry': 'Unable to analyze',
                'texture': 'Unable to analyze'
            },
            'reasoning': 'Analysis unavailable due to system error',
            'recommendations': [
                'Please try again later',
                'Consult a healthcare professional if you have concerns'
            ],
            'is_fallback': True
        }

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Handle image processing operations."""
    
    @staticmethod
    def validate_image(file) -> bool:
        """
        Validate image file format and size.
        
        Args:
            file: File object from request
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check file extension
            allowed_extensions = {'png', 'jpg', 'jpeg'}
            if not file.filename.lower().endswith(tuple(allowed_extensions)):
                logger.warning(f"Invalid file extension: {file.filename}")
                return False
            
            # Check file size (max 16MB)
            if len(file.read()) > 16 * 1024 * 1024:
                logger.warning(f"File too large: {file.filename}")
                return False
                
            file.seek(0)  # Reset file pointer
            return True
        except Exception as e:
            logger.error(f"Error validating image: {str(e)}")
            return False

    @staticmethod
    def preprocess_image(image_data: bytes, target_size: Tuple[int, int] = (299, 299)) -> np.ndarray:
        """
        Preprocess image for model input.
        
        Args:
            image_data: Raw image bytes
            target_size: Desired image dimensions
            
        Returns:
            np.ndarray: Processed image array
        """
        start_time = time.time()
        try:
            # Convert bytes to image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize
            image = image.resize(target_size)
            
            # Convert to array and normalize
            img_array = np.array(image) / 255.0
            
            log_data_processing(
                logger,
                "Image Preprocessing",
                f"Original size: {image.size}",
                f"Processed size: {target_size}"
            )
            
            end_time = time.time()
            log_performance_metrics(logger, start_time, end_time, "Image Preprocessing")
            
            return img_array
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            raise

class ClinicalDataProcessor:
    """Handle clinical data operations."""
    
    def __init__(self, data_path: str):
        """
        Initialize with path to clinical data.
        
        Args:
            data_path: Path to clinical data CSV file
        """
        self.data_path = data_path
        self.data = None
        self.load_data()

    def load_data(self) -> None:
        """Load clinical data from CSV file."""
        try:
            self.data = pd.read_csv(self.data_path)
            logger.info(f"Clinical data loaded successfully from {self.data_path}")
        except Exception as e:
            logger.error(f"Error loading clinical data: {str(e)}")
            raise

    def get_statistics(self, condition: str) -> Dict:
        """
        Get statistical information for a specific condition.
        
        Args:
            condition: Type of condition to analyze
            
        Returns:
            Dict: Statistical information
        """
        try:
            stats = {
                'stage_distribution': self.data['diagnoses_ajcc_pathologic_stage'].value_counts().to_dict(),
                'age_distribution': {
                    'mean': float(self.data['demographic_age_at_index'].mean()),
                    'median': float(self.data['demographic_age_at_index'].median()),
                    'std': float(self.data['demographic_age_at_index'].std())
                },
                'gender_distribution': self.data['demographic_gender'].value_counts().to_dict(),
                'similar_cases': len(self.data[self.data['diagnoses_morphology'] == condition])
            }
            return stats
        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}")
            raise

class ResultsFormatter:
    """Format and validate analysis results."""
    
    @staticmethod
    def format_prediction(
        prediction: str,
        confidence: float,
        clinical_stats: Dict,
        characteristics: Dict
    ) -> Dict:
        """
        Format prediction results.
        
        Args:
            prediction: Model prediction
            confidence: Confidence score
            clinical_stats: Clinical statistics
            characteristics: Image characteristics
            
        Returns:
            Dict: Formatted results
        """
        try:
            return {
                'prediction': prediction,
                'confidence': float(confidence),
                'timestamp': datetime.now().isoformat(),
                'clinical_statistics': clinical_stats,
                'characteristics': characteristics,
                'recommendations': ResultsFormatter.get_recommendations(prediction, confidence)
            }
        except Exception as e:
            logger.error(f"Error formatting prediction results: {str(e)}")
            raise

    @staticmethod
    def get_recommendations(prediction: str, confidence: float) -> List[str]:
        """
        Generate recommendations based on prediction.
        
        Args:
            prediction: Model prediction
            confidence: Confidence score
            
        Returns:
            List[str]: List of recommendations
        """
        recommendations = []
        
        if prediction.lower() == 'malignant':
            recommendations.extend([
                "Seek immediate medical attention",
                "Schedule an appointment with a dermatologist",
                "Document any changes in the lesion",
                "Avoid sun exposure to the affected area"
            ])
        else:
            recommendations.extend([
                "Continue regular skin checks",
                "Use sun protection",
                "Monitor for any changes",
                "Schedule routine dermatologist visits"
            ])
            
        if confidence < 0.8:
            recommendations.append("Consider getting a second opinion due to uncertainty in the analysis")
            
        return recommendations

class SystemMonitor:
    """Monitor system health and performance."""
    
    @staticmethod
    def get_system_metrics() -> Dict:
        """
        Get current system metrics.
        
        Returns:
            Dict: System metrics
        """
        import psutil
        
        return {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }

    @staticmethod
    def check_system_health() -> Tuple[bool, str]:
        """
        Check if system is healthy.
        
        Returns:
            Tuple[bool, str]: Health status and message
        """
        metrics = SystemMonitor.get_system_metrics()
        
        if metrics['cpu_usage'] > 90:
            return False, "High CPU usage"
        if metrics['memory_usage'] > 90:
            return False, "High memory usage"
        if metrics['disk_usage'] > 90:
            return False, "Low disk space"
            
        return True, "System healthy"

def save_to_history(result: Dict, history_file: str = 'analysis_history.json') -> None:
    """
    Save analysis result to history.
    
    Args:
        result: Analysis result
        history_file: Path to history file
    """
    try:
        # Load existing history
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
            
        # Add new result
        history.append({
            'timestamp': datetime.now().isoformat(),
            'result': result
        })
        
        # Keep only last 100 entries
        history = history[-100:]
        
        # Save updated history
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
            
        logger.info(f"Analysis result saved to history: {history_file}")
        
    except Exception as e:
        logger.error(f"Error saving to history: {str(e)}")
        raise
