/*
==============================================
Frontend JavaScript for Log Classification Dashboard
Frontend Engineer: Real-time updates, charts, interactions

Features:
- Real-time job monitoring via WebSocket
- Chart.js visualizations
- File upload with drag & drop
- Dynamic table updates
- Navigation management
==============================================
*/

// API Base URL
const API_BASE = window.location.origin;

// Current user data
let currentUser = null;
let authToken = null;

// Initialize dashboard on load
document.addEventListener('DOMContentLoaded', async () => {
    await initializeDashboard();
    setupEventListeners();
    setupCharts();
    loadDashboardData();
});

// Initialize dashboard
async function initializeDashboard() {
    // Check if user is authenticated
    authToken = localStorage.getItem('auth_token');
    
    if (!authToken) {
        window.location.href = '/login';
        return;
    }
    
    try {
        // Fetch current user
        const response = await fetch(`${API_BASE}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            currentUser = await response.json();
            document.getElementById('username').textContent = currentUser.full_name || currentUser.username;
            document.getElementById('user-role').textContent = currentUser.role;
        } else {
            logout();
        }
    } catch (error) {
        console.error('Failed to initialize:', error);
    }
}

// Setup event listeners
function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const target = item.getAttribute('href').substring(1);
            navigateTo(target);
        });
    });
    
    // File upload
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--primary)';
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = 'var(--border)';
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--border)';
        const file = e.dataTransfer.files[0];
        if (file && file.name.endsWith('.csv')) {
            handleFileSelect(file);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFileSelect(file);
        }
    });
}

// Navigation
function navigateTo(section) {
    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('href') === `#${section}`) {
            item.classList.add('active');
        }
    });
    
    // Update content sections
    document.querySelectorAll('.content-section').forEach(sec => {
        sec.classList.remove('active');
    });
    
    const targetSection = document.getElementById(`${section}-view`);
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Update page title
    const titles = {
        'dashboard': 'Dashboard Overview',
        'classify': 'Classify Logs',
        'jobs': 'Jobs History',
        'analytics': 'Analytics',
        'settings': 'Settings'
    };
    
    document.getElementById('page-title').textContent = titles[section] || 'Dashboard';
}

// Setup Charts
let methodsChart, categoriesChart;

function setupCharts() {
    // Methods Chart
    const methodsCtx = document.getElementById('methodsChart').getContext('2d');
    methodsChart = new Chart(methodsCtx, {
        type: 'doughnut',
        data: {
            labels: ['Regex', 'BERT', 'LLM'],
            datasets: [{
                data: [45, 40, 15],
                backgroundColor: [
                    '#6366f1',
                    '#10b981',
                    '#f59e0b'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#cbd5e1',
                        padding: 20,
                        font: {
                            size: 12
                        }
                    }
                }
            }
        }
    });
    
    // Categories Chart
    const categoriesCtx = document.getElementById('categoriesChart').getContext('2d');
    categoriesChart = new Chart(categoriesCtx, {
        type: 'bar',
        data: {
            labels: ['User Actions', 'System Notifications', 'File Operations', 'Errors', 'Other'],
            datasets: [{
                label: 'Log Count',
                data: [1200, 850, 640, 320, 180],
                backgroundColor: '#6366f1',
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#334155'
                    },
                    ticks: {
                        color: '#cbd5e1'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#cbd5e1'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Load dashboard data
async function loadDashboardData() {
    try {
        // Fetch metrics
        const metricsResponse = await fetch(`${API_BASE}/metrics`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (metricsResponse.ok) {
            const metrics = await metricsResponse.json();
            updateDashboardStats(metrics);
        }
        
        // Fetch recent jobs
        const jobsResponse = await fetch(`${API_BASE}/jobs?limit=5`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (jobsResponse.ok) {
            const jobs = await jobsResponse.json();
            updateRecentJobsTable(jobs);
        }
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
    }
}

// Update dashboard stats
function updateDashboardStats(metrics) {
    document.getElementById('total-logs').textContent = metrics.total_classifications.toLocaleString();
    document.getElementById('avg-time').textContent = `${Math.round(metrics.average_processing_time_ms)}ms`;
    document.getElementById('active-jobs').textContent = metrics.active_jobs || 0;
    
    // Update charts
    if (metrics.classifications_by_method) {
        methodsChart.data.datasets[0].data = [
            metrics.classifications_by_method.regex || 0,
            metrics.classifications_by_method.bert || 0,
            metrics.classifications_by_method.llm || 0
        ];
        methodsChart.update();
    }
}

// Update recent jobs table
function updateRecentJobsTable(jobs) {
    const tbody = document.getElementById('recent-jobs-table');
    tbody.innerHTML = '';
    
    jobs.forEach(job => {
        const row = document.createElement('tr');
        
        const statusClass = {
            'completed': 'success',
            'processing': 'warning',
            'failed': 'danger',
            'pending': 'info'
        }[job.status] || 'info';
        
        row.innerHTML = `
            <td><code>${job.job_id.substring(0, 8)}...</code></td>
            <td>${job.filename || 'N/A'}</td>
            <td>${job.total_logs}</td>
            <td><span class="badge badge-${statusClass}">${job.status}</span></td>
            <td>${job.processing_time || 'N/A'}</td>
            <td>
                <button class="btn-icon" onclick="viewJob('${job.job_id}')">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn-icon" onclick="downloadResults('${job.job_id}')">
                    <i class="fas fa-download"></i>
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// File handling
function handleFileSelect(file) {
    document.getElementById('dropZone').style.display = 'none';
    document.getElementById('fileInfo').style.display = 'flex';
    
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = formatBytes(file.size);
    
    window.selectedFile = file;
}

async function uploadFile() {
    if (!window.selectedFile) return;
    
    const formData = new FormData();
    formData.append('file', window.selectedFile);
    
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('processingStatus').style.display = 'block';
    
    try {
        const response = await fetch(`${API_BASE}/classify/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            
            // Poll for job status
            if (result.job_id) {
                pollJobStatus(result.job_id);
            } else {
                // Immediate result
                showSuccessMessage('Classification completed!');
                resetUploadForm();
            }
        } else {
            showErrorMessage('Upload failed. Please try again.');
            resetUploadForm();
        }
    } catch (error) {
        console.error('Upload error:', error);
        showErrorMessage('Upload failed. Please try again.');
        resetUploadForm();
    }
}

// Poll job status
async function pollJobStatus(jobId) {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/jobs/${jobId}/status`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            
            if (response.ok) {
                const status = await response.json();
                
                // Update progress
                const progress = (status.processed / status.total) * 100;
                document.getElementById('progressFill').style.width = `${progress}%`;
                document.getElementById('progressText').textContent = `Processing: ${Math.round(progress)}%`;
                
                if (status.status === 'completed') {
                    clearInterval(interval);
                    showSuccessMessage('Classification completed!');
                    resetUploadForm();
                    loadDashboardData();
                } else if (status.status === 'failed') {
                    clearInterval(interval);
                    showErrorMessage('Classification failed.');
                    resetUploadForm();
                }
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 2000);
}

// Utility functions
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function resetUploadForm() {
    document.getElementById('dropZone').style.display = 'block';
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('processingStatus').style.display = 'none';
    document.getElementById('progressFill').style.width = '0%';
    window.selectedFile = null;
}

function showSuccessMessage(message) {
    // Implement toast notification
    alert(message);
}

function showErrorMessage(message) {
    // Implement toast notification
    alert(message);
}

function viewJob(jobId) {
    // Navigate to job details
    console.log('View job:', jobId);
}

function downloadResults(jobId) {
    window.location.href = `${API_BASE}/jobs/${jobId}/download`;
}

function logout() {
    localStorage.removeItem('auth_token');
    window.location.href = '/login';
}

// Auto-refresh dashboard every 30 seconds
setInterval(loadDashboardData, 30000);
