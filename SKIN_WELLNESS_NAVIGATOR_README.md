# Skin Wellness Navigator

A web application for AI-driven skin lesion analysis to assist in early detection of potential skin cancers.

## Overview

The Skin Wellness Navigator is designed to help users analyze images of skin lesions using AI to determine if they appear benign or potentially malignant. This application provides:

- A user-friendly web interface for image upload
- Image preprocessing capabilities
- A backend API for classification
- Clear result visualization

## Project Structure

```
Skin Wellness Navigator/
├── server.py              # Flask backend server
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
│   └── index.html         # Main application page
├── static/                # Static assets
│   ├── css/
│   │   └── style.css      # Application styling
│   └── js/
│       └── main.js        # Frontend JavaScript
└── SKIN_WELLNESS_NAVIGATOR_README.md  # This file
```

## Setup and Installation

### Python Configuration (Windows)

If you encounter the error: `python: The term 'python' is not recognized...`, you need to add Python to your system PATH:

1. **Find Your Python Installation**:
   - Open Command Prompt and run: `where py` to locate your Python installation
   - Typically found in: `C:\Users\<username>\AppData\Local\Programs\Python\Python<version>` or `C:\Python<version>`

2. **Add Python to PATH**:
   - **Method 1: Using System Properties**:
     1. Right-click on 'This PC' or 'My Computer' and select 'Properties'
     2. Click on 'Advanced system settings'
     3. Click the 'Environment Variables' button
     4. Under 'System variables', find and select 'Path', then click 'Edit'
     5. Click 'New' and add the path to your Python installation (e.g., `C:\Python311`)
     6. Add another entry for the Scripts folder (e.g., `C:\Python311\Scripts`)
     7. Click 'OK' on all dialogs to save changes
   
   - **Method 2: Using Command Prompt (Administrative)**:
     ```
     setx PATH "%PATH%;C:\Path\to\Python;C:\Path\to\Python\Scripts" /M
     ```
     Replace `C:\Path\to\Python` with your actual Python installation path

3. **Verify the Configuration**:
   - Close and reopen Command Prompt
   - Run: `python --version` to confirm Python is recognized

### Installing Dependencies and Running the Application

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python server.py
   ```

3. **Access the Application**:
   Open a web browser and navigate to `http://127.0.0.1:5000`

### Troubleshooting

- If Python is still not recognized after updating PATH, try restarting your computer
- Ensure there are no typos in the PATH entries
- If using `py` works but `python` doesn't, you can create an alias by adding a python.bat file to a directory in your PATH with the content: `@py.exe %*`

## Future Model Integration

This application is currently set up with placeholder functions for AI model integration. To integrate an actual skin cancer classification model:

1. Update the `load_model()` function in `server.py` to load your trained model
2. Adjust the `preprocess_image()` function to match your model's required input format
3. Modify the `predict_skin_cancer()` function to use your model for making predictions

### Expected Model Requirements

When implementing a skin cancer classification model, consider:

- Input image size (currently set to 224x224 pixels)
- Color channel format (RGB)
- Pixel normalization method (currently dividing by 255.0)
- Output format (class labels and confidence scores)

## Disclaimer

This application is intended for educational and informational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of a qualified healthcare provider for any medical concerns.
