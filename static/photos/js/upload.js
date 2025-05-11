document.addEventListener('DOMContentLoaded', function() {
    // Initialize file input display
    document.getElementById('fileInput').addEventListener('change', function(e) {
        const fileList = document.getElementById('fileList');
        fileList.innerHTML = '';

        if (this.files.length > 0) {
            for (let i = 0; i < this.files.length; i++) {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';

                // Validate file size immediately
                const file = this.files[i];
                const isValid = validateFileSize(file.size);

                if (!isValid) {
                    fileItem.classList.add('invalid-file');
                }

                const fileName = document.createElement('span');
                fileName.className = 'file-name';
                fileName.textContent = `${i+1}. ${file.name}`;

                const fileSize = document.createElement('span');
                fileSize.className = 'file-size';
                fileSize.textContent = formatFileSize(file.size);

                // Add error message if invalid
                if (!isValid) {
                    const errorMsg = document.createElement('span');
                    errorMsg.className = 'file-error';
                    errorMsg.textContent = ' (Too large - will be skipped)';
                    fileName.appendChild(errorMsg);
                }

                fileItem.appendChild(fileName);
                fileItem.appendChild(fileSize);
                fileList.appendChild(fileItem);
            }
        }
    });
    // Upload button
    document.getElementById('uploadButton').addEventListener('click', uploadFiles);

    // File size validation helper
    function validateFileSize(bytes) {
        const maxSize = 5 * 1024 * 1024; // 5MB
        return bytes <= maxSize;
    }
    // File size formatter
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
    // CSRF Cookie helper
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Main upload function - UPDATED
    async function uploadFiles() {
        const fileInput = document.getElementById('fileInput');
        const fileList = document.getElementById('fileList');
        const uploadButton = document.getElementById('uploadButton');
        const statusDiv = document.getElementById('status');
        const resultsDiv = document.getElementById('results');
        const progressContainer = document.getElementById('progressContainer');
        const progressBar = document.getElementById('progressBar');

        // Client-side validation
        const files = Array.from(fileInput.files);
        const invalidFiles = files.filter(file => !validateFileSize(file.size));

        if (files.length === 0) {
            statusDiv.textContent = 'Please select files first!';
            statusDiv.className = 'error';
            return;
        }

        // UI Preparation
        uploadButton.disabled = true;
        uploadButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
        statusDiv.className = 'processing';
        resultsDiv.innerHTML = '';
        progressContainer.style.display = 'block';
        progressBar.style.width = '0%';

        // Show validation summary
        if (invalidFiles.length > 0) {
            statusDiv.innerHTML = `Processing ${files.length - invalidFiles.length} files (<span class="error-text">${invalidFiles.length} files skipped due to size</span>)...`;

            // Highlight invalid files in the list
            invalidFiles.forEach(file => {
                const fileItems = fileList.querySelectorAll('.file-item');
                fileItems.forEach(item => {
                    if (item.textContent.includes(file.name)) {
                        item.classList.add('invalid-file');
                    }
                });
            });
        } else {
            statusDiv.textContent = `Processing ${files.length} files...`;
        }

        try {
            const formData = new FormData();
            // Only add valid files to FormData
            files.filter(file => validateFileSize(file.size)).forEach(file => {
                formData.append('images', file);
            });

            const response = await fetch('/api/upload/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                credentials: 'include',
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Upload failed');
            }

            const data = await response.json();

            if (data.task_ids && data.valid_images) {
                monitorTasks(data.task_ids, data.valid_images);
            } else {
                throw new Error('Invalid server response format');
            }

        } catch (error) {
            statusDiv.innerHTML = `Error: ${error.message}`;
            statusDiv.className = 'error';
            resetUploadButton();
            progressContainer.style.display = 'none';
        }
    }

    // Task monitoring - now matches task IDs with their filenames
    async function monitorTasks(taskIds, validImageNames) {
        const statusDiv = document.getElementById('status');
        const resultsDiv = document.getElementById('results');
        const progressBar = document.getElementById('progressBar');
        const uploadButton = document.getElementById('uploadButton');

        let completedTasks = 0;
        const totalTasks = taskIds.length;
        const processedTasks = new Set();

        const checkStatus = async () => {
            try {
                const results = await Promise.all(
                    taskIds.map(id =>
                        fetch(`/api/task-status/?task_id=${id}`)
                            .then(res => res.json())
                            .catch(() => ({ status: 'FAILURE' }))
                    )
                );

                // Update progress based on ACTUAL tasks created (not original files)
                const newCompleted = results.filter(r => r.status === 'SUCCESS' || r.status === 'FAILURE').length;
                if (newCompleted > completedTasks) {
                    completedTasks = newCompleted;
                    const progress = Math.min(100, Math.round((completedTasks / totalTasks) * 100));
                    progressBar.style.width = `${progress}%`;
                }

                // Process results with proper filename matching
                results.forEach((res, index) => {
                    if ((res.status === 'SUCCESS' || res.status === 'FAILURE') && !processedTasks.has(taskIds[index])) {
                        processedTasks.add(taskIds[index]);

                        const resultDiv = document.createElement('div');
                        resultDiv.className = 'result-item';
                        resultDiv.id = `task-${taskIds[index]}`;

                        // Get the corresponding filename
                        const fileName = validImageNames[index] || `File ${index + 1}`;

                        if (res.status === 'SUCCESS') {
                            resultDiv.innerHTML = `
                                <p><strong>File:</strong> ${fileName}</p>
                                <p><strong>Status:</strong> <span class="success">Success</span></p>
                                ${res.result?.file_name ? `<p><strong>Processed As:</strong> ${res.result.file_name}</p>` : ''}
                                ${res.result?.image_random_num ? `<p><strong>Result:</strong> ${res.result.image_random_num}</p>` : ''}
                            `;
                        } else {
                            resultDiv.innerHTML = `
                                <p><strong>File:</strong> ${fileName}</p>
                                <p><strong>Status:</strong> <span class="error">Failed</span></p>
                                <p><strong>Error:</strong> ${res.error || 'Unknown error'}</p>
                            `;
                        }

                        resultsDiv.appendChild(resultDiv);
                    }
                });

                // Check completion
                if (completedTasks >= totalTasks) {
                    statusDiv.textContent = 'All tasks completed!';
                    statusDiv.className = 'success';
                    resetUploadButton();
                } else {
                    setTimeout(checkStatus, 2000);
                }

            } catch (error) {
                console.error('Status check error:', error);
                statusDiv.textContent = 'Error checking task status';
                statusDiv.className = 'error';
                resetUploadButton();
            }
        };

        checkStatus();
    }

    // Helper function to reset upload button
    function resetUploadButton() {
        const uploadButton = document.getElementById('uploadButton');
        uploadButton.disabled = false;
        uploadButton.innerHTML = '<i class="fas fa-upload"></i> Upload Files';
    }
});