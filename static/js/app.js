// SmartFile AI Frontend JavaScript

class SmartFileAI {
    constructor() {
        this.currentFile = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadStats();
        this.loadCategories();
        this.setupDragAndDrop();
    }

    setupEventListeners() {
        // Search input enter key
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.searchFiles();
            }
        });

        // File input change
        document.getElementById('fileInput').addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files);
        });

        // Smooth scrolling for navigation
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    setupDragAndDrop() {
        const uploadArea = document.getElementById('uploadArea');

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            this.handleFileUpload(files);
        });

        uploadArea.addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    }

    async searchFiles() {
        const query = document.getElementById('searchInput').value.trim();
        if (!query) {
            this.showAlert('Please enter a search query', 'warning');
            return;
        }

        this.showLoading(true);
        const resultsContainer = document.getElementById('searchResults');

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });

            const data = await response.json();

            if (response.ok) {
                this.displaySearchResults(data.results, data.query);
            } else {
                this.showAlert(data.error || 'Search failed', 'danger');
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showAlert('Search failed. Please try again.', 'danger');
        } finally {
            this.showLoading(false);
        }
    }

    displaySearchResults(results, query) {
        const resultsContainer = document.getElementById('searchResults');
        
        if (results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    No files found matching "${query}"
                </div>
            `;
            return;
        }

        let html = `
            <div class="mb-3">
                <h6>Found ${results.length} file(s) matching "${query}"</h6>
            </div>
        `;

        results.forEach((result, index) => {
            const highlightedSnippet = this.highlightSearchTerms(result.snippet, query);
            const fileIcon = this.getFileIcon(result.file_type);
            
            html += `
                <div class="search-result" style="animation-delay: ${index * 0.1}s">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div class="d-flex align-items-center">
                            <i class="${fileIcon} file-icon ${result.file_type}"></i>
                            <div>
                                <div class="filename">${this.escapeHtml(result.filename)}</div>
                                <div class="file-path">${this.escapeHtml(result.file_path)}</div>
                            </div>
                        </div>
                        <div class="d-flex align-items-center">
                            <span class="category-badge me-2">${result.category}</span>
                            ${result.is_encrypted ? '<i class="fas fa-lock text-warning me-2"></i>' : ''}
                        </div>
                    </div>
                    
                    <div class="snippet">${highlightedSnippet}</div>
                    
                    <div class="d-flex justify-content-between align-items-center mt-3">
                        <div class="keywords">
                            ${result.keywords.map(keyword => 
                                `<span class="keyword-tag">${this.escapeHtml(keyword)}</span>`
                            ).join('')}
                        </div>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="app.previewFile('${this.escapeHtml(JSON.stringify(result))}')">
                                <i class="fas fa-eye"></i> Preview
                            </button>
                            <button class="btn btn-outline-success" onclick="app.openFileDirect('${this.escapeHtml(result.file_path)}')">
                                <i class="fas fa-external-link-alt"></i> Open
                            </button>
                            ${!result.is_encrypted ? `
                                <button class="btn btn-outline-warning" onclick="app.encryptFileDirect('${this.escapeHtml(result.file_path)}')">
                                    <i class="fas fa-lock"></i> Encrypt
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        });

        resultsContainer.innerHTML = html;
    }

    highlightSearchTerms(text, query) {
        if (!text) return '';
        
        const terms = query.toLowerCase().split(/\s+/);
        let highlightedText = this.escapeHtml(text);
        
        terms.forEach(term => {
            if (term.length > 2) {
                const regex = new RegExp(`(${term})`, 'gi');
                highlightedText = highlightedText.replace(regex, '<span class="highlight">$1</span>');
            }
        });
        
        return highlightedText;
    }

    getFileIcon(fileType) {
        const iconMap = {
            'pdf': 'fas fa-file-pdf',
            'docx': 'fas fa-file-word',
            'txt': 'fas fa-file-alt',
            'jpg': 'fas fa-file-image',
            'jpeg': 'fas fa-file-image',
            'png': 'fas fa-file-image',
            'mp3': 'fas fa-file-audio',
            'wav': 'fas fa-file-audio',
            'm4a': 'fas fa-file-audio'
        };
        
        return iconMap[fileType] || 'fas fa-file';
    }

    async handleFileUpload(files) {
        if (files.length === 0) return;

        const uploadStatus = document.getElementById('uploadStatus');
        const uploadProgress = document.getElementById('uploadProgress');
        const progressBar = uploadProgress.querySelector('.progress-bar');

        uploadStatus.innerHTML = '';
        uploadProgress.classList.remove('d-none');

        let uploadedCount = 0;
        const totalFiles = files.length;

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (response.ok) {
                    uploadedCount++;
                    const progress = (uploadedCount / totalFiles) * 100;
                    progressBar.style.width = `${progress}%`;

                    uploadStatus.innerHTML += `
                        <div class="alert alert-success alert-sm">
                            <i class="fas fa-check-circle me-2"></i>
                            ${file.name} uploaded successfully
                            <br><small>Category: ${data.category} | Keywords: ${data.keywords.slice(0, 5).join(', ')}</small>
                        </div>
                    `;
                } else {
                    uploadStatus.innerHTML += `
                        <div class="alert alert-danger alert-sm">
                            <i class="fas fa-exclamation-circle me-2"></i>
                            Failed to upload ${file.name}: ${data.error}
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Upload error:', error);
                uploadStatus.innerHTML += `
                    <div class="alert alert-danger alert-sm">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Failed to upload ${file.name}: Network error
                    </div>
                `;
            }
        }

        // Refresh stats and categories after upload
        setTimeout(() => {
            this.loadStats();
            this.loadCategories();
            uploadProgress.classList.add('d-none');
            progressBar.style.width = '0%';
        }, 1000);
    }

    async startVoiceSearch() {
        if (this.isRecording) {
            this.stopVoiceRecording();
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                await this.processVoiceCommand(audioBlob);
                
                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            this.updateVoiceUI(true);

        } catch (error) {
            console.error('Voice recording error:', error);
            this.showAlert('Failed to access microphone. Please check permissions.', 'danger');
        }
    }

    stopVoiceRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.updateVoiceUI(false);
        }
    }

    updateVoiceUI(isRecording) {
        const voiceButton = document.querySelector('.btn-success');
        const voiceStatus = document.getElementById('voiceStatus');
        const voiceStatusText = document.getElementById('voiceStatusText');

        if (isRecording) {
            voiceButton.innerHTML = '<i class="fas fa-stop me-2"></i>Stop Recording';
            voiceButton.classList.add('recording');
            voiceStatus.classList.remove('d-none');
            voiceStatusText.textContent = 'Listening... Speak now!';
        } else {
            voiceButton.innerHTML = '<i class="fas fa-microphone me-2"></i>Voice Search';
            voiceButton.classList.remove('recording');
            voiceStatus.classList.add('d-none');
        }
    }

    async processVoiceCommand(audioBlob) {
        this.showLoading(true);

        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'voice_command.wav');

            const response = await fetch('/api/voice_command', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                document.getElementById('searchInput').value = data.command;
                this.displaySearchResults(data.results, data.command);
                this.showAlert(`Voice command recognized: "${data.command}"`, 'success');
            } else {
                this.showAlert(data.error || 'Voice command failed', 'danger');
            }
        } catch (error) {
            console.error('Voice command error:', error);
            this.showAlert('Voice command failed. Please try again.', 'danger');
        } finally {
            this.showLoading(false);
        }
    }

    previewFile(fileData) {
        try {
            const file = typeof fileData === 'string' ? JSON.parse(fileData) : fileData;
            this.currentFile = file;

            const modal = new bootstrap.Modal(document.getElementById('filePreviewModal'));
            const previewContent = document.getElementById('filePreviewContent');

            previewContent.innerHTML = `
                <div class="file-preview">
                    <div class="preview-item">
                        <div class="preview-label">Filename:</div>
                        <div class="preview-value">${this.escapeHtml(file.filename)}</div>
                    </div>
                    <div class="preview-item">
                        <div class="preview-label">File Path:</div>
                        <div class="preview-value">${this.escapeHtml(file.file_path)}</div>
                    </div>
                    <div class="preview-item">
                        <div class="preview-label">File Type:</div>
                        <div class="preview-value">${file.file_type.toUpperCase()}</div>
                    </div>
                    <div class="preview-item">
                        <div class="preview-label">Category:</div>
                        <div class="preview-value">${file.category}</div>
                    </div>
                    <div class="preview-item">
                        <div class="preview-label">File Size:</div>
                        <div class="preview-value">${this.formatFileSize(file.file_size)}</div>
                    </div>
                    <div class="preview-item">
                        <div class="preview-label">Summary:</div>
                        <div class="preview-value">${this.escapeHtml(file.summary)}</div>
                    </div>
                    <div class="preview-item">
                        <div class="preview-label">Keywords:</div>
                        <div class="preview-value">
                            ${file.keywords.map(keyword => 
                                `<span class="keyword-tag">${this.escapeHtml(keyword)}</span>`
                            ).join(' ')}
                        </div>
                    </div>
                    <div class="preview-item">
                        <div class="preview-label">Security Status:</div>
                        <div class="preview-value">
                            ${file.is_encrypted ? 
                                '<i class="fas fa-lock text-warning"></i> Encrypted' : 
                                '<i class="fas fa-unlock text-success"></i> Not Encrypted'}
                        </div>
                    </div>
                </div>
            `;

            modal.show();
        } catch (error) {
            console.error('Preview error:', error);
            this.showAlert('Failed to preview file', 'danger');
        }
    }

    async openFileDirect(filePath) {
        try {
            const response = await fetch('/api/open_file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ file_path: filePath })
            });

            const data = await response.json();

            if (response.ok) {
                this.showAlert(data.message, 'success');
            } else {
                this.showAlert(data.error || 'Failed to open file', 'danger');
            }
        } catch (error) {
            console.error('Open file error:', error);
            this.showAlert('Failed to open file', 'danger');
        }
    }

    async encryptFileDirect(filePath) {
        try {
            const response = await fetch('/api/encrypt_file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ file_path: filePath })
            });

            const data = await response.json();

            if (response.ok) {
                this.showAlert(data.message, 'success');
                // Refresh search results if any
                const searchInput = document.getElementById('searchInput').value;
                if (searchInput) {
                    this.searchFiles();
                }
            } else {
                this.showAlert(data.error || 'Failed to encrypt file', 'danger');
            }
        } catch (error) {
            console.error('Encrypt file error:', error);
            this.showAlert('Failed to encrypt file', 'danger');
        }
    }

    async loadStats() {
        try {
            const response = await fetch('/api/get_stats');
            const stats = await response.json();

            if (response.ok) {
                this.displayStats(stats);
            }
        } catch (error) {
            console.error('Stats error:', error);
        }
    }

    displayStats(stats) {
        const statsContainer = document.getElementById('statsContainer');
        
        let html = `
            <div class="col-md-3 col-sm-6 mb-3">
                <div class="stat-card">
                    <div class="stat-number">${stats.total_files || 0}</div>
                    <div class="stat-label">Total Files</div>
                </div>
            </div>
        `;

        // Display top file types
        const topFileTypes = Object.entries(stats.file_types || {})
            .sort(([,a], [,b]) => b - a)
            .slice(0, 3);

        topFileTypes.forEach(([type, count]) => {
            html += `
                <div class="col-md-3 col-sm-6 mb-3">
                    <div class="stat-card">
                        <div class="stat-number">${count}</div>
                        <div class="stat-label">${type.toUpperCase()} Files</div>
                    </div>
                </div>
            `;
        });

        statsContainer.innerHTML = html;
    }

    async loadCategories() {
        try {
            const response = await fetch('/api/get_categories');
            const data = await response.json();

            if (response.ok) {
                this.displayCategories(data.categories);
            }
        } catch (error) {
            console.error('Categories error:', error);
        }
    }

    displayCategories(categories) {
        const categoriesContainer = document.getElementById('categoriesContainer');
        
        if (!categories || categories.length === 0) {
            categoriesContainer.innerHTML = '<p class="text-muted">No categories available</p>';
            return;
        }

        let html = '';
        categories.forEach(category => {
            html += `
                <div class="col-md-4 col-sm-6 mb-3">
                    <div class="category-card">
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="category-name">
                                <i class="fas fa-folder me-2"></i>
                                ${category}
                            </div>
                            <span class="category-count">0 files</span>
                        </div>
                    </div>
                </div>
            `;
        });

        categoriesContainer.innerHTML = html;
    }

    showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert at the top of the container
        const container = document.querySelector('.container-fluid');
        container.insertBefore(alertDiv, container.firstChild);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    showLoading(show) {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (show) {
            loadingOverlay.classList.remove('d-none');
        } else {
            loadingOverlay.classList.add('d-none');
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global functions for inline event handlers
function searchFiles() {
    app.searchFiles();
}

function startVoiceSearch() {
    app.startVoiceSearch();
}

function openFile() {
    if (app.currentFile) {
        app.openFileDirect(app.currentFile.file_path);
    }
}

function encryptFile() {
    if (app.currentFile) {
        app.encryptFileDirect(app.currentFile.file_path);
    }
}

// Initialize the application
const app = new SmartFileAI();
