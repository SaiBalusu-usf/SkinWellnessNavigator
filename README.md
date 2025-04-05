# Skin Wellness Navigator

An AI-powered web application for skin lesion analysis and classification using NIH datasets and clinical data integration. This tool helps in the early assessment of skin conditions by providing instant analysis and recommendations.

## Features

### AI-Powered Analysis
- Real-time skin lesion classification (benign/malignant)
- Confidence score calculation
- Integration with NIH clinical datasets
- Stage distribution analysis
- Morphology type classification
- Similar cases comparison

### Clinical Data Analysis
- Patient demographics analysis
- Disease characteristics assessment
- Treatment outcome tracking
- Statistical visualizations including:
  - Age distribution
  - Gender distribution
  - Disease stage distribution

### Interactive Web Interface
- Drag-and-drop image upload
- Real-time analysis progress tracking
- Dark/light theme support
- Responsive design for all devices
- Interactive results visualization
- Analysis history tracking
- Report export functionality

## Technical Stack

### Backend
- Flask web server
- Python data processing
- Pandas for clinical data analysis
- PIL for image processing
- NumPy for numerical computations

### Frontend
- HTML5/CSS3
- Modern JavaScript (ES6+)
- Responsive design
- FontAwesome icons
- Google Fonts integration

### Data Processing
- Clinical data analysis using Pandas
- Image preprocessing pipeline
- Statistical analysis tools
- Data visualization using Matplotlib and Seaborn

## Project Structure

```
SkinWellnessNavigator/
├── templates/
│   ├── index.html              # Main web interface
│   └── static/
│       ├── css/
│       │   └── styles.css      # Application styles
│       └── js/
│           └── main.js         # Frontend functionality
├── analyze_clinical.py         # Clinical data analysis
├── server.py                   # Flask server and AI endpoint
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd SkinWellnessNavigator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the server:
```bash
py server.py
```

4. Access the application at:
```
http://localhost:5000
```

## Dependencies

Core dependencies include:
- Flask >= 2.0.1
- Pillow >= 10.0.0
- NumPy >= 1.22.0
- Pandas >= 2.0.0
- TensorFlow >= 2.8.0
- PyTorch >= 1.11.0
- Scikit-learn >= 1.0.2
- OpenCV-Python >= 4.7.0

For a complete list, see `requirements.txt`

## Clinical Data Integration

The application integrates with clinical datasets to provide comprehensive analysis:
- Patient demographics
- Disease characteristics
- Treatment outcomes
- Stage distribution
- Morphology types

## Analysis Features

### Image Analysis
- Image preprocessing and normalization
- Lesion classification
- Confidence score calculation
- Similar case matching

### Results Provided
- Classification (Benign/Malignant)
- Confidence percentage
- Risk level assessment
- Stage distribution analysis
- Similar cases statistics
- Personalized recommendations

### Data Visualization
- Stage distribution charts
- Confidence level indicators
- Historical trend analysis
- Comparative analysis views

## Security and Privacy

- Local data processing
- No external data storage
- HIPAA compliance considerations
- Secure file handling
- Privacy-first approach

## Important Notes

1. **Medical Disclaimer**: This tool is designed for preliminary assessment only and should not replace professional medical diagnosis. Always consult healthcare professionals for proper diagnosis and treatment.

2. **Development Status**: The current implementation uses simulated AI responses. Integration with actual AI models requires additional setup.

3. **Data Requirements**: The system expects clinical data in CSV format with specific column structures. See `clinical.csv` for reference.

## Performance Metrics

Based on validation dataset:
- Accuracy: 95%
- Sensitivity: 93%
- Specificity: 97%

*Note: These metrics are placeholder values and should be updated with actual model performance data.*

## Future Enhancements

Planned improvements include:
- Integration with deep learning models
- Enhanced visualization options
- Additional clinical data sources
- Mobile application development
- API endpoint documentation
- Enhanced reporting features

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests for any enhancements.

## License

[Add License Information]

## Contact

[Add Contact Information]
