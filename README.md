# Skin Wellness Navigator

This repository is a demonstration of a Flask image upload interface backed by a Gemini request. It is not validated for diagnosis or clinical use. No accuracy, sensitivity, or specificity has been established for this application.

## How the demo works

The browser uploads an image to the Flask server. `server.py` sends the image bytes to Google's Gemini service for analysis. Processing is therefore **not local**. Do not upload real patient images or sensitive health information to this demo. If the model is unavailable or fails, the API returns HTTP 503 with `status: "analysis_unavailable"`; it does not issue a classification or confidence score.

The repository includes clinical CSV files used for demonstration statistics. Their provenance, permissions, and suitability for any intended use need independent review. The code does not establish that the Gemini model was trained on these files or on an NIH dataset.

## Local setup with synthetic test images

1. Install the dependencies listed in `requirements.txt`.
2. Copy `.env.example` to a local `.env` file and set `GEMINI_API_KEY` only if you intend to make external Gemini requests. Never commit the local file. Without a configured key, analysis reports unavailable.
3. Run `python server.py` and open `http://localhost:5000`.

Tests and demonstrations should use synthetic images and mocked model responses. Do not run this demo with real patient data.

## Security follow-up

An earlier commit tracked a Gemini API key in `.env`. Removing the file from the current tree does not invalidate that key or erase Git history. The owner must revoke the exposed key in Google AI Studio or Google Cloud credentials, review usage, and configure any replacement privately. This change does not rewrite repository history.
