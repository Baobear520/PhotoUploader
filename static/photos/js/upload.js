document.addEventListener('DOMContentLoaded', function() {
    // Initialize file input display
    document.getElementById('fileInput').addEventListener('change', function(e) {
        const fileList = document.getElementById('fileList');
        fileList.innerHTML = '';

        if (this.files.length > 0) {
            for (let i = 0; i < this.files.length; i++) {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';

                const fileName = document.createElement('span');
                fileName.className = 'file-name';
                fileName.textContent = `${i+1}. ${this.files[i].name}`;

                const fileSize = document.createElement('span');
                fileSize.className = 'file-size';
                fileSize.textContent = formatFileSize(this.files[i].size);

                fileItem.appendChild(fileName);
                fileItem.appendChild(fileSize);
                fileList.appendChild(fileItem);
            }
        }
    });

    // Set up upload button
    document.getElementById('uploadButton').addEventListener('click', uploadFiles);

    // File size formatter
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Main upload function
    async function uploadFiles() {
        const fileInput = document.getElementById('fileInput');
        const uploadButton = document.getElementById('uploadButton');
        const statusDiv = document.getElementById('status');
        const resultsDiv = document.getElementById('results');
        const progressContainer = document.getElementById('progressContainer');
        const progressBar = document.getElementById('progressBar');

        // Validation
        if (fileInput.files.length === 0) {
            statusDiv.textContent = 'Please select files first!';
            statusDiv.className = 'error';
            return;
        }

        // UI Preparation
        uploadButton.disabled = true;
        uploadButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
        statusDiv.textContent = 'Preparing files for upload...';
        statusDiv.className = 'processing';
        resultsDiv.innerHTML = '';
        progressContainer.style.display = 'block';
        progressBar.style.width = '0%';

        // Prepare FormData
        const formData = new FormData();
        for (const file of fileInput.files) {
            formData.append('images', file);
        }

        try {
            // Send to server
            const response = await fetch('/api/upload/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Upload failed');
            }

            const data = await response.json();
            statusDiv.textContent = `Processing ${data.task_ids.length} files...`;
            monitorTasks(data.task_ids, fileInput.files.length);

        } catch (error) {
            console.error('Upload error:', error);
            statusDiv.textContent = `Error: ${error.message}`;
            statusDiv.className = 'error';
            uploadButton.disabled = false;
            uploadButton.innerHTML = '<i class="fas fa-upload"></i> Upload Files';
            progressContainer.style.display = 'none';
        }
    }

    // Task monitoring
    async function monitorTasks(taskIds, totalFiles) {
        const statusDiv = document.getElementById('status');
        const resultsDiv = document.getElementById('results');
        const progressBar = document.getElementById('progressBar');
        const uploadButton = document.getElementById('uploadButton');

        let completedTasks = 0;
        const processedTasks = new Set();

        const checkStatus = async () => {
            try {
                const results = await Promise.all(
                    taskIds.map(id =>
                        fetch(`/api/task-status/?task_id=${id}`)
                            .then(res => res.json())
                            .catch(() => ({ status: 'FAILURE' }))
                ));

                // Update progress
                const newCompleted = results.filter(r => r.status === 'SUCCESS' || r.status === 'FAILURE').length;
                if (newCompleted > completedTasks) {
                    completedTasks = newCompleted;
                    const progress = Math.min(100, Math.round((completedTasks / totalFiles) * 100));
                    progressBar.style.width = `${progress}%`;
                }

                // Process results
                results.forEach((res, index) => {
                    if ((res.status === 'SUCCESS' || res.status === 'FAILURE') && !processedTasks.has(taskIds[index])) {
                        processedTasks.add(taskIds[index]);

                        const resultDiv = document.createElement('div');
                        resultDiv.className = 'result-item';

                        if (res.status === 'SUCCESS') {
                            resultDiv.innerHTML = `
                                <p><strong>File:</strong> ${res.result.file_name}</p>
                                <p><strong>Status:</strong> <span style="color: #28a745">Success</span></p>
                                <p><strong>ID:</strong> ${res.result.id}</p>
                                <p><strong>Random Num:</strong> ${res.result.image_random_num}</p>
                                <p><strong>Processing Time:</strong> ${res.result.execution_time.toFixed(2)}s</p>
                            `;
                        } else {
                            resultDiv.innerHTML = `
                                <p><strong>Task ID:</strong> ${taskIds[index]}</p>
                                <p><strong>Status:</strong> <span style="color: #dc3545">Failed</span></p>
                                <p><strong>Error:</strong> ${res.error || 'Unknown error'}</p>
                            `;
                        }

                        resultsDiv.appendChild(resultDiv);
                    }
                });

                // Check completion
                if (completedTasks === totalFiles) {
                    statusDiv.textContent = 'All tasks completed!';
                    statusDiv.className = 'success';
                    uploadButton.disabled = false;
                    uploadButton.innerHTML = '<i class="fas fa-upload"></i> Upload Files';
                } else {
                    setTimeout(checkStatus, 5000);
                }

            } catch (error) {
                console.error('Status check error:', error);
                statusDiv.textContent = 'Error checking task status';
                statusDiv.className = 'error';
                uploadButton.disabled = false;
                uploadButton.innerHTML = '<i class="fas fa-upload"></i> Upload Files';
            }
        };

        checkStatus();
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
});