# Skin Wellness Navigator: demo guide

This interface is an unvalidated demonstration and must not be used to diagnose, triage, or make treatment decisions. Its displayed output has no established clinical accuracy.

The browser sends an uploaded image to the Flask server, which passes the image bytes to Google's Gemini service. Images are therefore shared with an external provider; the application does not perform all processing locally. Do not upload real patient images or sensitive health information.

When the model is unavailable or fails, the app displays **Analysis unavailable**. It does not provide a diagnostic label or confidence score in that case.

The clinical CSV files in this repository have not had their provenance, permissions, and suitability verified here. Their presence does not demonstrate model training or clinical validation. Use synthetic images and mocked responses for tests and demonstrations.

For local setup, follow [README.md](README.md). Any API key belongs in an ignored local environment file or a private secret store, never in a commit. The previously exposed key requires owner revocation; deleting a file from the current branch does not remove it from Git history.
