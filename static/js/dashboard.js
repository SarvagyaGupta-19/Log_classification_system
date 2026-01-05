// LogClassifier Pro - Professional UI/UX JavaScript
// Production-Ready with Full State Management

const API = window.location.origin;
let currentFile = null;
let classificationResult = null;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Log Classification System');
    initializeApp();
    loadMetrics();
});

function initializeApp() {
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.getElementById('uploadArea');
    const browseBtn = document.getElementById('browseBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const classifyBtn = document.getElementById('classifyBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const newUploadBtn = document.getElementById('newUploadBtn');

    // File input handlers
    fileInput.addEventListener('change', handleFileSelect);
    
    // Browse button handler
    browseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.value = ''; // Reset input to allow re-selecting same file
        fileInput.click();
    });
    
    // Drag and drop handlers
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--primary)';
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = 'var(--border)';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--border)';
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect({ target: { files } });
        }
    });

    // Action button handlers
    cancelBtn.addEventListener('click', resetToUpload);
    classifyBtn.addEventListener('click', startClassification);
    downloadBtn.addEventListener('click', downloadResults);
    newUploadBtn.addEventListener('click', resetToUpload);
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    
    if (!file) return;
    
    // Validate file type - accept CSV and raw log files
    const allowedExtensions = ['.csv', '.log', '.txt', '.json', '.jsonl'];
    const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!allowedExtensions.includes(fileExt)) {
        showToast('Please upload a CSV, LOG, TXT, or JSON file', 'error');
        return;
    }
    
    // Validate file size (max 50MB)
    if (file.size > 50 * 1024 * 1024) {
        showToast('File too large. Maximum size is 50MB', 'error');
        return;
    }
    
    currentFile = file;
    showFileSelected();
}

function showFileSelected() {
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    
    fileName.textContent = currentFile.name;
    fileSize.textContent = formatFileSize(currentFile.size);
    
    // Update UI state
    document.getElementById('uploadArea').style.display = 'none';
    document.getElementById('fileSelected').style.display = 'block';
}

async function startClassification() {
    if (!currentFile) return;
    
    // Show processing state
    document.getElementById('fileSelected').style.display = 'none';
    document.getElementById('processing').style.display = 'block';
    
    const formData = new FormData();
    formData.append('file', currentFile);
    
    // Start progress animation
    animateProgress();
    
    try {
        const response = await fetch(`${API}/classify/`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Classification failed');
        }
        
        classificationResult = await response.json();
        
        // Complete progress
        completeProgress();
        
        // Show success state after animation
        setTimeout(() => {
            showSuccessState();
            showAnalytics();
            loadMetrics();
        }, 1000);
        
    } catch (error) {
        console.error('Classification error:', error);
        showToast('Classification failed. Please try again.', 'error');
        resetToUpload();
    }
}

function animateProgress() {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    let progress = 0;
    
    // Animate to 90%
    const interval = setInterval(() => {
        progress += 2;
        if (progress <= 90) {
            progressBar.style.width = progress + '%';
            
            if (progress < 30) {
                progressText.textContent = 'Initializing classification engine...';
            } else if (progress < 60) {
                progressText.textContent = 'Processing log entries...';
            } else {
                progressText.textContent = 'Analyzing severity levels...';
            }
        } else {
            clearInterval(interval);
        }
    }, 100);
    
    // Store interval for cleanup if needed
    window.progressInterval = interval;
}

function completeProgress() {
    if (window.progressInterval) {
        clearInterval(window.progressInterval);
    }
    
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    
    // Animate to 100%
    progressBar.style.width = '95%';
    progressText.textContent = 'Finalizing results...';
    
    setTimeout(() => {
        progressBar.style.width = '100%';
        progressText.textContent = 'Classification complete!';
    }, 300);
}

function showSuccessState() {
    document.getElementById('processing').style.display = 'none';
    document.getElementById('successState').style.display = 'block';
    
    // Update success message
    const message = document.getElementById('successMessage');
    if (classificationResult) {
        const total = classificationResult.total_logs || 0;
        const stats = classificationResult.severity_stats || {};
        const high = (stats.CRITICAL || 0) + (stats.HIGH || 0);
        message.textContent = `Successfully processed ${total.toLocaleString()} log entries. ${high} high-priority issues identified.`;
        
        // Show column mapping info if available
        if (classificationResult.column_mapping) {
            showColumnMappingInfo(classificationResult.column_mapping);
        }
    }
    
    showToast('Classification completed successfully', 'success');
}

function showColumnMappingInfo(mappingInfo) {
    // Display column mapping information to user
    let message = '';
    
    if (mappingInfo.warnings && mappingInfo.warnings.length > 0) {
        message += 'Note: ';
        message += mappingInfo.warnings.join(', ');
        console.log('Column mapping:', mappingInfo);
        
        // Show info toast if columns were auto-detected
        if (mappingInfo.warnings.some(w => w.includes('Auto-detected') || w.includes('no source'))) {
            showToast('CSV columns automatically mapped', 'success');
        }
    }
}

function showAnalytics() {
    if (!classificationResult) {
        console.warn('No classification result available');
        return;
    }
    
    console.log('Classification result:', classificationResult);
    
    const stats = classificationResult.severity_stats || {};
    const categoryStats = classificationResult.category_stats || {};
    
    // Update severity counts (handle both formats)
    document.getElementById('criticalCount').textContent = stats.CRITICAL || 0;
    document.getElementById('highCount').textContent = stats.HIGH || 0;
    document.getElementById('mediumCount').textContent = stats.MEDIUM || 0;
    document.getElementById('lowCount').textContent = stats.LOW || 0;
    document.getElementById('infoCount').textContent = stats.INFO || 0;
    document.getElementById('unclassifiedCount').textContent = stats.UNCLASSIFIED || 0;
    
    console.log('Updated severity counts:', stats);
    
    // Update category breakdown
    updateCategoryBreakdown(categoryStats);
    
    // Show analytics section with smooth animation
    const analyticsSection = document.getElementById('analyticsSection');
    analyticsSection.style.display = 'block';
    
    // Smooth scroll to analytics
    setTimeout(() => {
        analyticsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 500);
}

function updateCategoryBreakdown(categoryStats) {
    const categoryList = document.getElementById('categoryList');
    
    if (!categoryStats || Object.keys(categoryStats).length === 0) {
        categoryList.innerHTML = '<p style="text-align: center; color: var(--text-muted); padding: 2rem;">No category data available</p>';
        return;
    }
    
    // Sort categories by count
    const sortedCategories = Object.entries(categoryStats)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 10); // Top 10 categories
    
    categoryList.innerHTML = sortedCategories.map(([category, count]) => `
        <div class="category-item">
            <span class="category-name">${category}</span>
            <span class="category-count">${count}</span>
        </div>
    `).join('');
}

async function downloadResults() {
    try {
        showToast('Preparing download...', 'info');
        
        const response = await fetch(`${API}/download/`);
        
        if (!response.ok) {
            throw new Error('Download failed');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        
        // Generate filename with timestamp
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
        link.href = url;
        link.download = `classified_logs_${timestamp}.csv`;
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Cleanup
        window.URL.revokeObjectURL(url);
        
        showToast('Download started successfully!', 'success');
        
    } catch (error) {
        console.error('Download error:', error);
        showToast('Download failed. Please try again.', 'error');
    }
}

function resetToUpload() {
    currentFile = null;
    classificationResult = null;
    
    // Reset file input
    document.getElementById('fileInput').value = '';
    
    // Reset progress
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('progressText').textContent = 'Initializing BERT model...';
    
    // Hide all states except upload
    document.getElementById('uploadArea').style.display = 'block';
    document.getElementById('fileSelected').style.display = 'none';
    document.getElementById('processing').style.display = 'none';
    document.getElementById('successState').style.display = 'none';
    
    // Keep analytics visible if they exist
    // User might want to compare with previous results
}

async function loadMetrics() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch(`${API}/metrics`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
            const data = await response.json();
            if (data.total_classifications !== undefined) {
                document.getElementById('totalLogs').textContent = 
                    data.total_classifications.toLocaleString();
            }
        }
    } catch (error) {
        if (error.name !== 'AbortError') {
            console.log('Metrics loading failed:', error.message);
        }
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3500);
}

// Make functions globally accessible
window.resetToUpload = resetToUpload;
window.downloadResults = downloadResults;
