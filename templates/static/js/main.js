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

// Image preview and validation
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

// Tips carousel with fade effect
const tips = [
    "Apply sunscreen daily, even on cloudy days",
    "Stay hydrated for healthy skin",
    "Get 7-8 hours of sleep for skin regeneration",
    "Eat a balanced diet rich in antioxidants",
    "Cleanse your face twice daily",
    "Use gentle, non-comedogenic products",
    "Protect your skin from excessive sun exposure",
    "Don't forget to moisturize daily"
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

// History tracking with local storage
const analysisHistory = JSON.parse(localStorage.getItem('analysisHistory') || '[]');

function saveToHistory(result) {
    const history = {
        date: new Date().toISOString(),
        result: result
    };
    analysisHistory.unshift(history);
    if (analysisHistory.length > 5) analysisHistory.pop();
    localStorage.setItem('analysisHistory', JSON.stringify(analysisHistory));
    updateHistoryDisplay();
}

function updateHistoryDisplay() {
    const historyContainer = document.getElementById('history-container');
    if (!historyContainer) return;
    
    if (analysisHistory.length === 0) {
        historyContainer.innerHTML = '<p class="no-history">No analysis history yet</p>';
        return;
    }
    
    historyContainer.innerHTML = analysisHistory.map(item => `
        <div class="history-item">
            <div class="history-date">${new Date(item.date).toLocaleDateString()}</div>
            <div class="history-result">
                <strong>Skin Type:</strong> ${item.result.skinType}<br>
                <strong>Hydration:</strong> ${item.result.hydration}<br>
                <strong>UV Damage:</strong> ${item.result.uvDamage}
            </div>
            <button class="btn btn-sm" onclick="exportReport(${JSON.stringify(item.result)})">
                <i class="fas fa-download"></i> Export
            </button>
        </div>
    `).join('');
}

// Export report functionality
function exportReport(result) {
    const reportData = {
        date: new Date().toLocaleDateString(),
        result: result
    };
    
    const reportText = `
Skin Wellness Report
Generated on: ${reportData.date}

Analysis Results:
- Skin Type: ${result.skinType}
- Hydration Level: ${result.hydration}
- UV Damage: ${result.uvDamage}

Recommendations:
${result.recommendations.map(rec => '- ' + rec).join('\n')}

Next Steps:
1. Follow the recommended skincare routine
2. Monitor changes in your skin condition
3. Schedule regular skin checkups
4. Use recommended products consistently

Note: This report is generated based on AI analysis and should be used as a general guide.
Please consult with a dermatologist for professional medical advice.
    `.trim();
    
    const blob = new Blob([reportText], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `skin-wellness-report-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Handle file upload and analysis
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('upload-area');
    const imageInput = document.getElementById('image-input');
    const browseBtn = document.getElementById('browse-btn');
    const uploadForm = document.getElementById('upload-form');
    const loading = document.getElementById('loading');
    const result = document.getElementById('result');

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
            imageInput.files = files;
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
        loading.style.display = 'block';
        analysisProgress = 0;
        updateProgress();

        // Simulate analysis (replace with actual API call)
        setTimeout(() => {
            loading.style.display = 'none';
            const analysisResult = {
                skinType: 'Normal to Combination',
                hydration: 'Good',
                uvDamage: 'Minimal',
                recommendations: [
                    'Continue with regular moisturizing',
                    'Use SPF 30+ sunscreen daily',
                    'Consider adding vitamin C serum to your routine',
                    'Maintain consistent cleansing routine'
                ]
            };
            displayResult(analysisResult);
            saveToHistory(analysisResult);
            showNotification('Analysis complete!', 'success');
        }, 3000);
    }

    function displayResult(analysisResult) {
        result.innerHTML = `
            <div class="result-card">
                <h3><i class="fas fa-check-circle"></i> Analysis Complete</h3>
                <div class="result-grid">
                    <div class="result-item">
                        <h4>Skin Type</h4>
                        <p>${analysisResult.skinType}</p>
                    </div>
                    <div class="result-item">
                        <h4>Hydration Level</h4>
                        <p>${analysisResult.hydration}</p>
                    </div>
                    <div class="result-item">
                        <h4>UV Damage</h4>
                        <p>${analysisResult.uvDamage}</p>
                    </div>
                </div>
                <div class="recommendations">
                    <h4>Recommendations</h4>
                    <ul>
                        ${analysisResult.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
                <div class="result-actions">
                    <button class="btn" onclick="exportReport(${JSON.stringify(analysisResult)})">
                        <i class="fas fa-download"></i> Export Report
                    </button>
                </div>
            </div>
        `;
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
