// Theme handling
const themeToggle = document.getElementById('theme-toggle');
const body = document.body;
const themeIcon = themeToggle.querySelector('i');

function toggleTheme() {
    body.classList.toggle('dark-theme');
    const isDark = body.classList.contains('dark-theme');
    localStorage.setItem('dark-theme', isDark);
    themeIcon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
}

// Initialize theme
if (localStorage.getItem('dark-theme') === 'true') {
    body.classList.add('dark-theme');
    themeIcon.className = 'fas fa-sun';
}

themeToggle.addEventListener('click', toggleTheme);

// Image analysis and handling
async function analyzeImage(file) {
    const formData = new FormData();
    formData.append('image', file);

    try {
        showLoading();
        updateProgress();

        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });

        const results = await response.json();
        if (results.status === 'analysis_unavailable') {
            displayResult(results);
            showNotification('Analysis is unavailable. Please try again later.', 'warning');
            return;
        }
        if (!response.ok) {
            throw new Error('Analysis failed');
        }

        displayResult(results);
        saveToHistory(results);
        showNotification('Analysis complete!', 'success');
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error analyzing image. Please try again.', 'error');
    } finally {
        hideLoading();
    }
}

function handleImagePreview(file) {
    const preview = document.getElementById('image-preview');
    const reader = new FileReader();
    
    reader.onload = function(e) {
        preview.innerHTML = `
            <div class="preview-container">
                <img src="${e.target.result}" alt="Preview" class="preview-image">
                <div class="preview-overlay">
                    <button class="btn btn-danger" onclick="removePreview()">Remove</button>
                </div>
            </div>
        `;
        preview.style.display = 'block';
        document.querySelector('.progress-container').style.display = 'block';
    };
    
    if (file) {
        reader.readAsDataURL(file);
    }
}

function removePreview() {
    const preview = document.getElementById('image-preview');
    const input = document.getElementById('image-input');
    preview.innerHTML = '';
    preview.style.display = 'none';
    input.value = '';
    document.querySelector('.progress-container').style.display = 'none';
}

// Progress tracking
let analysisProgress = 0;
const progressBar = document.getElementById('analysis-progress');

function updateProgress() {
    if (analysisProgress < 100) {
        analysisProgress += 10;
        progressBar.style.width = analysisProgress + '%';
        progressBar.setAttribute('aria-valuenow', analysisProgress);
        setTimeout(updateProgress, 200);
    }
}

function showLoading() {
    document.getElementById('loading').style.display = 'block';
    analysisProgress = 0;
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// Display analysis results
function displayResult(results) {
    const result = document.getElementById('result');
    if (results.status === 'analysis_unavailable') {
        result.innerHTML = '<div class="result-card"><h3>Analysis unavailable</h3><p>Analysis is unavailable. Please try again later.</p></div>';
        return;
    }
    const confidencePercentage = (results.confidence * 100).toFixed(1);
    
    result.innerHTML = `
        <div class="result-card">
            <h3>Analysis Complete</h3>
            
            <div class="result-grid">
                <div class="result-item">
                    <h4>Classification</h4>
                    <p>${results.prediction}</p>
                    <div class="confidence-bar">
                        <div class="confidence-level" style="width: ${confidencePercentage}%"></div>
                    </div>
                    <small>Confidence: ${confidencePercentage}%</small>
                </div>
                
                <div class="result-item">
                    <h4>Similar Cases</h4>
                    <p>${results.clinical_insights && results.clinical_insights.similar_cases ? results.clinical_insights.similar_cases : 'N/A'} cases</p>
                </div>
                
                <div class="result-item">
                    <h4>Common Morphology</h4>
                    <p>${results.clinical_insights && results.clinical_insights.common_morphology ? results.clinical_insights.common_morphology : 'N/A'}</p>
                </div>
            </div>

            <div class="characteristics-section">
                <h4>Lesion Characteristics</h4>
                <div class="characteristics-grid">
                    ${Object.entries(results.characteristics || {}).map(([key, value]) => `
                        <div class="characteristic-item">
                            <strong>${key.charAt(0).toUpperCase() + key.slice(1)}:</strong>
                            <span>${value}</span>
                        </div>
                    `).join('')}
                </div>
            </div>

            ${results.clinical_insights && results.clinical_insights.stage_distribution ? `
            <div class="stage-distribution">
                <h4>Stage Distribution</h4>
                <div class="stage-bars">
                    ${Object.entries(results.clinical_insights.stage_distribution)
                        .map(([stage, count]) => `
                            <div class="stage-bar-item">
                                <div class="stage-label">${stage}</div>
                                <div class="stage-bar">
                                    <div class="stage-bar-fill" style="width: ${(count / Math.max(...Object.values(results.clinical_insights.stage_distribution))) * 100}%"></div>
                                </div>
                                <div class="stage-count">${count}</div>
                            </div>
                        `).join('')}
                </div>
            </div>
            ` : ''}

            <div class="reasoning-section">
                <h4>Analysis Reasoning</h4>
                <p>${results.reasoning || 'No detailed reasoning available.'}</p>
            </div>

            <div class="recommendations">
                <h4>Recommendations</h4>
                <ul>
                    ${results.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
            </div>

            <div class="result-actions">
                <button class="btn" onclick='exportReport(${JSON.stringify(results).replace(/'/g, "\\'")})'">
                    <i class="fas fa-download"></i> Export Report
                </button>
                <button class="btn btn-secondary" onclick="window.location.reload()">
                    <i class="fas fa-redo"></i> New Analysis
                </button>
            </div>
        </div>
    `;
}

// History tracking
const analysisHistory = JSON.parse(localStorage.getItem('analysisHistory') || '[]');

function saveToHistory(results) {
    const history = {
        date: new Date().toISOString(),
        results: results
    };
    analysisHistory.unshift(history);
    if (analysisHistory.length > 5) analysisHistory.pop();
    localStorage.setItem('analysisHistory', JSON.stringify(analysisHistory));
    updateHistoryDisplay();
}

function updateHistoryDisplay() {
    const historyContainer = document.getElementById('history-container');
    if (!historyContainer) return;
    
    const validHistory = analysisHistory.filter(item =>
        item.results && !item.results.using_fallback &&
        item.results.status !== 'analysis_unavailable' &&
        typeof item.results.prediction === 'string' &&
        typeof item.results.confidence === 'number'
    );
    if (validHistory.length !== analysisHistory.length) {
        analysisHistory.splice(0, analysisHistory.length, ...validHistory);
        localStorage.setItem('analysisHistory', JSON.stringify(analysisHistory));
    }
    if (analysisHistory.length === 0) {
        historyContainer.innerHTML = '<p class="no-history">No analysis history yet</p>';
        return;
    }
    
    historyContainer.innerHTML = analysisHistory.map(item => `
        <div class="history-item ${item.results.prediction.toLowerCase()}-prediction">
            <div class="history-date">${new Date(item.date).toLocaleDateString()}</div>
            <div class="history-result">
                <strong>Classification:</strong> ${item.results.prediction}<br>
                <strong>Confidence:</strong> ${(item.results.confidence * 100).toFixed(1)}%
            </div>
            <div class="history-actions">
                <button class="btn btn-sm" onclick="exportReport(${JSON.stringify(item.results)})">
                    <i class="fas fa-download"></i> Export
                </button>
                <button class="btn btn-sm btn-secondary" onclick="showDetails(${JSON.stringify(item.results)})">
                    <i class="fas fa-info-circle"></i> Details
                </button>
            </div>
        </div>
    `).join('');
}

// Export report functionality
function exportReport(results) {
    const reportData = {
        date: new Date().toLocaleDateString(),
        results: results
    };
    
    const reportText = `
Skin Wellness Navigator demo result
Generated on: ${reportData.date}

Classification: ${results.prediction}
Confidence: ${(results.confidence * 100).toFixed(1)}%

This is an unvalidated demonstration, not a medical diagnosis.
`.trim();

    const blob = new Blob([reportText], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `skin-analysis-report-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Tips carousel
const tips = [
    "Regular skin checks can help detect issues early",
    "Use sunscreen daily to prevent UV damage",
    "Document any changes in moles or skin lesions",
    "Schedule regular dermatologist visits",
    "Know your skin cancer risk factors",
    "Protect your skin from excessive sun exposure",
    "Learn the ABCDE rule for melanoma detection",
    "Keep track of your skin examination history"
];

let currentTip = 0;

function showNextTip() {
    const tipElement = document.getElementById('skin-tip');
    tipElement.style.opacity = '0';
    
    setTimeout(() => {
        currentTip = (currentTip + 1) % tips.length;
        tipElement.textContent = tips[currentTip];
        tipElement.style.opacity = '1';
    }, 500);
}

// Initialize tips carousel
setInterval(showNextTip, 5000);

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('upload-area');
    const imageInput = document.getElementById('image-input');
    const browseBtn = document.getElementById('browse-btn');
    
    // Initialize history display
    updateHistoryDisplay();

    // Handle drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type.startsWith('image/')) {
            handleImageUpload(files[0]);
        } else {
            showNotification('Please upload an image file', 'error');
        }
    });

    // Handle browse button click
    browseBtn.addEventListener('click', () => {
        imageInput.click();
    });

    imageInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleImageUpload(e.target.files[0]);
        }
    });

    function handleImageUpload(file) {
        if (!file.type.startsWith('image/')) {
            showNotification('Please upload an image file', 'error');
            return;
        }

        handleImagePreview(file);
        analyzeImage(file);
    }
});

// Notifications system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }, 100);
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(tooltip => {
        tooltip.addEventListener('mouseenter', e => {
            const tip = document.createElement('div');
            tip.className = 'tooltip';
            tip.textContent = e.target.getAttribute('data-tooltip');
            document.body.appendChild(tip);
            
            const rect = e.target.getBoundingClientRect();
            tip.style.top = rect.top - tip.offsetHeight - 10 + 'px';
            tip.style.left = rect.left + (rect.width - tip.offsetWidth) / 2 + 'px';
            
            e.target.addEventListener('mouseleave', () => tip.remove(), { once: true });
        });
    });
});
