/**
 * Multi-domain Remote Sensing Detection System - Frontend Logic
 */

// State management
const state = {
    sessionId: null,
    taskId: null,
    selectedTasks: new Set(),
    uploadedFiles: [],
    eventSource: null
};

// DOM Elements
const elements = {
    fileInput: document.getElementById('fileInput'),
    uploadArea: document.getElementById('uploadArea'),
    fileList: document.getElementById('fileList'),
    uploadStatus: document.getElementById('uploadStatus'),
    taskList: document.getElementById('taskList'),
    cityName: document.getElementById('cityName'),
    // VL 模型配置
    vlBaseUrl: document.getElementById('vlBaseUrl'),
    vlApiKey: document.getElementById('vlApiKey'),
    vlModel: document.getElementById('vlModel'),
    // LLM 模型配置
    llmBaseUrl: document.getElementById('llmBaseUrl'),
    llmApiKey: document.getElementById('llmApiKey'),
    llmModel: document.getElementById('llmModel'),
    // SAM2 模型配置
    sam2Url: document.getElementById('sam2Url'),
    sam2Model: document.getElementById('sam2Model'),
    // 按钮和面板
    startBtn: document.getElementById('startBtn'),
    stopBtn: document.getElementById('stopBtn'),
    progressSection: document.getElementById('progressSection'),
    progressBar: document.getElementById('progressBar'),
    progressText: document.getElementById('progressText'),
    currentFile: document.getElementById('currentFile'),
    logPanel: document.getElementById('logPanel'),
    resultsSection: document.getElementById('resultsSection'),
    statsCards: document.getElementById('statsCards'),
    samplesGrid: document.getElementById('samplesGrid'),
    downloadReport: document.getElementById('downloadReport'),
    newDetection: document.getElementById('newDetection'),
    welcomeSection: document.getElementById('welcomeSection')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadTasks();
    setupEventListeners();
});

// Load available detection tasks
async function loadTasks() {
    try {
        const response = await fetch('/api/detection/tasks');
        const tasks = await response.json();

        elements.taskList.innerHTML = tasks.map(task => `
            <label class="task-item" data-task-id="${task.id}">
                <input type="checkbox" value="${task.id}">
                <div class="task-info">
                    <div class="task-name">${task.name}</div>
                    <div class="task-desc">${task.description}</div>
                </div>
            </label>
        `).join('');

        // Add click handlers
        elements.taskList.querySelectorAll('.task-item').forEach(item => {
            const checkbox = item.querySelector('input[type="checkbox"]');
            item.addEventListener('click', (e) => {
                if (e.target !== checkbox) {
                    checkbox.checked = !checkbox.checked;
                }
                item.classList.toggle('selected', checkbox.checked);

                if (checkbox.checked) {
                    state.selectedTasks.add(checkbox.value);
                } else {
                    state.selectedTasks.delete(checkbox.value);
                }
                updateStartButton();
            });
        });
    } catch (error) {
        console.error('Failed to load tasks:', error);
        elements.taskList.innerHTML = '<p class="error">加载任务列表失败</p>';
    }
}

// Setup event listeners
function setupEventListeners() {
    // File upload
    elements.fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    elements.uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.uploadArea.classList.add('dragover');
    });

    elements.uploadArea.addEventListener('dragleave', () => {
        elements.uploadArea.classList.remove('dragover');
    });

    elements.uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFiles(e.dataTransfer.files);
        }
    });

    // Input validation
    [elements.cityName, elements.vlBaseUrl, elements.vlApiKey, elements.vlModel,
     elements.llmBaseUrl, elements.llmApiKey, elements.llmModel].forEach(input => {
        input.addEventListener('input', updateStartButton);
    });

    // Buttons
    elements.startBtn.addEventListener('click', startDetection);
    elements.stopBtn.addEventListener('click', stopDetection);
    elements.newDetection.addEventListener('click', resetDetection);
    elements.downloadReport.addEventListener('click', downloadReport);
}

// Handle file selection
function handleFileSelect(e) {
    handleFiles(e.target.files);
}

// Handle files
async function handleFiles(files) {
    if (files.length === 0) return;

    const formData = new FormData();
    let validCount = 0;

    for (const file of files) {
        const ext = file.name.split('.').pop().toLowerCase();
        if (['jpg', 'jpeg', 'png', 'tif', 'tiff', 'bmp'].includes(ext)) {
            formData.append('files', file);
            validCount++;
        }
    }

    if (validCount === 0) {
        showUploadStatus('没有找到有效的图像文件', true);
        return;
    }

    showUploadStatus(`正在上传 ${validCount} 个文件...`);

    try {
        const response = await fetch('/api/upload/images', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        const result = await response.json();
        state.sessionId = result.session_id;
        state.uploadedFiles = result.files;

        showUploadStatus(`成功上传 ${result.file_count} 个文件`);
        displayFileList(result.files);
        updateStartButton();
    } catch (error) {
        showUploadStatus(`上传失败: ${error.message}`, true);
    }
}

// Display uploaded file list
function displayFileList(files) {
    const maxDisplay = 5;
    const displayFiles = files.slice(0, maxDisplay);

    elements.fileList.innerHTML = displayFiles.map(file => `
        <div class="file-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
            </svg>
            <span>${file}</span>
        </div>
    `).join('');

    if (files.length > maxDisplay) {
        elements.fileList.innerHTML += `
            <div class="file-item">
                <span>... 还有 ${files.length - maxDisplay} 个文件</span>
            </div>
        `;
    }
}

// Show upload status
function showUploadStatus(message, isError = false) {
    elements.uploadStatus.textContent = message;
    elements.uploadStatus.className = 'upload-status' + (isError ? ' error' : '');
}

// Update start button state
function updateStartButton() {
    const canStart = state.sessionId &&
        state.selectedTasks.size > 0 &&
        elements.cityName.value.trim() &&
        elements.vlBaseUrl.value.trim() &&
        elements.vlApiKey.value.trim() &&
        elements.vlModel.value.trim() &&
        elements.llmBaseUrl.value.trim() &&
        elements.llmApiKey.value.trim() &&
        elements.llmModel.value.trim();

    elements.startBtn.disabled = !canStart;
}

// Start detection
async function startDetection() {
    const request = {
        session_id: state.sessionId,
        tasks: Array.from(state.selectedTasks),
        city_name: elements.cityName.value.trim(),
        // VL 模型配置
        vl_base_url: elements.vlBaseUrl.value.trim(),
        vl_api_key: elements.vlApiKey.value.trim(),
        vl_model: elements.vlModel.value.trim(),
        // LLM 模型配置
        llm_base_url: elements.llmBaseUrl.value.trim(),
        llm_api_key: elements.llmApiKey.value.trim(),
        llm_model: elements.llmModel.value.trim(),
        // SAM2 模型配置 (可选，不需要 API Key)
        sam2_url: elements.sam2Url.value.trim() || null,
        sam2_api_key: null,
        sam2_model: elements.sam2Model.value.trim() || null
    };

    try {
        elements.startBtn.disabled = true;
        elements.startBtn.textContent = '启动中...';

        const response = await fetch('/api/detection/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to start detection');
        }

        const result = await response.json();
        state.taskId = result.task_id;

        // Show progress section
        elements.welcomeSection.style.display = 'none';
        elements.progressSection.style.display = 'block';
        elements.resultsSection.style.display = 'none';
        elements.startBtn.style.display = 'none';
        elements.stopBtn.style.display = 'block';

        // Clear log panel
        elements.logPanel.innerHTML = '';
        addLog('任务已创建', 'info');

        // Start SSE connection with polling fallback
        connectProgressStream();
        startPolling();
    } catch (error) {
        elements.startBtn.disabled = false;
        elements.startBtn.textContent = '开始检测';
        addLog(`启动失败: ${error.message}`, 'error');
        alert(`启动检测失败: ${error.message}`);
    }
}

// Polling interval ID
let pollingInterval = null;

// Start polling as fallback
function startPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }

    pollingInterval = setInterval(async () => {
        if (!state.taskId) {
            clearInterval(pollingInterval);
            return;
        }

        try {
            const response = await fetch(`/api/detection/status/${state.taskId}`);
            if (response.ok) {
                const data = await response.json();

                // Update progress display
                const percentage = data.progress || 0;
                elements.progressBar.style.width = `${percentage}%`;
                elements.progressText.textContent = `${Math.round(percentage)}%`;

                if (data.current_file) {
                    elements.currentFile.textContent = `当前文件: ${data.current_file}`;
                }

                // Check if task is complete
                if (['completed', 'failed', 'stopped'].includes(data.status)) {
                    clearInterval(pollingInterval);
                    pollingInterval = null;

                    if (state.eventSource) {
                        state.eventSource.close();
                        state.eventSource = null;
                    }

                    elements.stopBtn.style.display = 'none';

                    if (data.status === 'completed') {
                        addLog('检测任务完成!', 'success');
                        loadResults();
                    } else if (data.status === 'failed') {
                        addLog(`任务失败: ${data.error || '未知错误'}`, 'error');
                        elements.startBtn.style.display = 'block';
                        elements.startBtn.disabled = false;
                        elements.startBtn.textContent = '重新检测';
                    } else if (data.status === 'stopped') {
                        addLog('任务已停止', 'info');
                        elements.startBtn.style.display = 'block';
                        elements.startBtn.disabled = false;
                        elements.startBtn.textContent = '重新检测';
                    }
                }
            }
        } catch (e) {
            console.error('Polling error:', e);
        }
    }, 3000); // Poll every 3 seconds
}

// Connect to SSE progress stream
function connectProgressStream() {
    if (state.eventSource) {
        state.eventSource.close();
    }

    state.eventSource = new EventSource(`/api/detection/progress/${state.taskId}`);

    state.eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            if (data.error) {
                addLog(`错误: ${data.error}`, 'error');
                return;
            }

            updateProgress(data);
        } catch (e) {
            console.error('Failed to parse progress event:', e);
        }
    };

    state.eventSource.onerror = (error) => {
        console.error('SSE connection error:', error);
        if (state.eventSource) {
            state.eventSource.close();
            state.eventSource = null;
        }
        // Polling will continue as fallback
    };
}

// Update progress display
function updateProgress(data) {
    const percentage = data.percentage || 0;

    elements.progressBar.style.width = `${percentage}%`;
    elements.progressText.textContent = `${data.current}/${data.total} (${percentage}%)`;

    if (data.current_file) {
        elements.currentFile.textContent = `当前文件: ${data.current_file}`;
    }

    addLog(data.message, 'info');

    // Check if task is complete
    if (['completed', 'failed', 'stopped'].includes(data.status)) {
        if (state.eventSource) {
            state.eventSource.close();
            state.eventSource = null;
        }

        elements.stopBtn.style.display = 'none';

        if (data.status === 'completed') {
            addLog('检测任务完成!', 'success');
            loadResults();
        } else if (data.status === 'failed') {
            addLog(`任务失败: ${data.message}`, 'error');
            elements.startBtn.style.display = 'block';
            elements.startBtn.disabled = false;
            elements.startBtn.textContent = '重新检测';
        } else if (data.status === 'stopped') {
            addLog('任务已停止', 'info');
            elements.startBtn.style.display = 'block';
            elements.startBtn.disabled = false;
            elements.startBtn.textContent = '重新检测';
        }
    }
}

// Add log entry
function addLog(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.innerHTML = `<span class="timestamp">[${timestamp}]</span>${message}`;
    elements.logPanel.appendChild(entry);
    elements.logPanel.scrollTop = elements.logPanel.scrollHeight;
}

// Stop detection
async function stopDetection() {
    if (!state.taskId) return;

    try {
        const response = await fetch(`/api/detection/stop/${state.taskId}`, {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to stop task');
        }

        addLog('正在停止任务...', 'info');
    } catch (error) {
        addLog(`停止失败: ${error.message}`, 'error');
    }
}

// Load detection results
async function loadResults() {
    try {
        const response = await fetch(`/api/results/${state.sessionId}?task_id=${state.taskId}`);

        if (!response.ok) {
            throw new Error('Failed to load results');
        }

        const results = await response.json();
        displayResults(results);

        // Load report content
        loadReport();

        // Load sample images
        loadSamples();
    } catch (error) {
        addLog(`加载结果失败: ${error.message}`, 'error');
    }
}

// Load and display report
async function loadReport() {
    const reportContent = document.getElementById('reportContent');
    if (!reportContent) return;

    reportContent.innerHTML = '<div class="report-loading">加载报告中...</div>';

    try {
        const response = await fetch(`/api/results/${state.sessionId}/report`);

        if (!response.ok) {
            reportContent.innerHTML = '<div class="report-loading">暂无报告</div>';
            return;
        }

        const markdown = await response.text();

        // Simple markdown to HTML conversion
        const html = markdownToHtml(markdown);
        reportContent.innerHTML = html;

    } catch (error) {
        console.error('Failed to load report:', error);
        reportContent.innerHTML = '<div class="report-loading">加载报告失败</div>';
    }
}

// Simple markdown to HTML converter
function markdownToHtml(markdown) {
    let html = markdown
        // Escape HTML
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        // Headers
        .replace(/^#### (.+)$/gm, '<h4>$1</h4>')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        // Bold
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        // Code blocks
        .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
        // Inline code
        .replace(/`(.+?)`/g, '<code>$1</code>')
        // Unordered lists
        .replace(/^\s*[-*]\s+(.+)$/gm, '<li>$1</li>')
        // Ordered lists
        .replace(/^\s*\d+\.\s+(.+)$/gm, '<li>$1</li>')
        // Horizontal rule
        .replace(/^---$/gm, '<hr>')
        // Line breaks
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');

    // Wrap in paragraph
    html = '<p>' + html + '</p>';

    // Clean up empty paragraphs
    html = html.replace(/<p>\s*<\/p>/g, '');
    html = html.replace(/<p>\s*<h/g, '<h');
    html = html.replace(/<\/h(\d)>\s*<\/p>/g, '</h$1>');
    html = html.replace(/<p>\s*<hr>\s*<\/p>/g, '<hr>');
    html = html.replace(/<p>\s*<pre>/g, '<pre>');
    html = html.replace(/<\/pre>\s*<\/p>/g, '</pre>');

    // Wrap consecutive li elements in ul
    html = html.replace(/(<li>.*?<\/li>)+/gs, '<ul>$&</ul>');

    return html;
}

// Display results
function displayResults(results) {
    elements.resultsSection.style.display = 'block';

    const stats = results.statistics || {};

    elements.statsCards.innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${stats.total_images || 0}</div>
            <div class="stat-label">总图像数</div>
        </div>
        <div class="stat-card highlight">
            <div class="stat-value">${stats.detected_count || 0}</div>
            <div class="stat-label">检测到目标</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${stats.detection_rate || 0}%</div>
            <div class="stat-label">检测率</div>
        </div>
    `;

    if (results.report_path) {
        elements.downloadReport.style.display = 'flex';
    }
}

// Load sample images
async function loadSamples() {
    try {
        const response = await fetch(`/api/results/${state.sessionId}/samples?limit=6`);

        if (!response.ok) {
            throw new Error('Failed to load samples');
        }

        const data = await response.json();
        displaySamples(data.samples);
    } catch (error) {
        console.error('Failed to load samples:', error);
    }
}

// Display sample images
function displaySamples(samples) {
    if (!samples || samples.length === 0) {
        elements.samplesGrid.innerHTML = '<p>暂无样例图片</p>';
        return;
    }

    elements.samplesGrid.innerHTML = samples.map(sample => `
        <div class="sample-item">
            <div class="sample-header">
                <span class="sample-filename">${sample.filename}</span>
                <span class="sample-badge ${sample.detected ? 'detected' : 'not-detected'}">
                    ${sample.detected ? '已检测' : '未检测'}
                </span>
            </div>
            <div class="sample-images">
                <div class="sample-img-container">
                    <img src="${sample.original}" alt="原图" onerror="this.src='/static/img/placeholder.png'">
                    <div class="sample-img-label">原图</div>
                </div>
                <div class="sample-img-container">
                    <img src="${sample.processed}" alt="处理后" onerror="this.src='/static/img/placeholder.png'">
                    <div class="sample-img-label">处理后</div>
                </div>
            </div>
        </div>
    `).join('');
}

// Download report as ZIP with images
async function downloadReport() {
    if (!state.sessionId) return;

    try {
        // Download ZIP file with report and images
        window.location.href = `/api/results/${state.sessionId}/report/download`;
    } catch (error) {
        alert(`下载报告失败: ${error.message}`);
    }
}

// Reset detection for new task
function resetDetection() {
    // Close SSE connection
    if (state.eventSource) {
        state.eventSource.close();
        state.eventSource = null;
    }

    // Clear polling
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }

    // Reset state
    state.sessionId = null;
    state.taskId = null;
    state.selectedTasks.clear();
    state.uploadedFiles = [];

    // Reset UI
    elements.fileInput.value = '';
    elements.fileList.innerHTML = '';
    elements.uploadStatus.textContent = '';
    elements.cityName.value = '';

    // Uncheck all tasks
    elements.taskList.querySelectorAll('.task-item').forEach(item => {
        item.classList.remove('selected');
        item.querySelector('input[type="checkbox"]').checked = false;
    });

    // Reset buttons
    elements.startBtn.style.display = 'block';
    elements.startBtn.disabled = true;
    elements.startBtn.textContent = '开始检测';
    elements.stopBtn.style.display = 'none';

    // Reset panels
    elements.progressSection.style.display = 'none';
    elements.resultsSection.style.display = 'none';
    elements.welcomeSection.style.display = 'flex';
    elements.logPanel.innerHTML = '';
    elements.progressBar.style.width = '0%';
    elements.progressText.textContent = '0%';
    elements.currentFile.textContent = '';
    elements.downloadReport.style.display = 'none';
}
