class DjangoAIBuilder {
    constructor() {
        this.apiBase = '/api';
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
        this.currentProject = null;
        this.currentFile = null;
        this.editor = null;
        
        this.init();
    }

    async init() {
        // Check if user is authenticated
        if (this.accessToken && await this.verifyToken()) {
            this.showMainApp();
        } else {
            this.showLoginModal();
        }
        
        this.setupEventListeners();
        this.initializeEditor();
    }

    async verifyToken() {
        try {
            const response = await fetch('/auth/profile/', {
                headers: {
                    'Authorization': `Bearer ${this.accessToken}`,
                    'Content-Type': 'application/json'
                }
            });
            if (response.ok) {
                const user = await response.json();
                document.getElementById('user-info').textContent = `Welcome, ${user.username}!`;
                return true;
            }
        } catch (error) {
            console.error('Token verification failed:', error);
        }
        return false;
    }

    async refreshAccessToken() {
        if (!this.refreshToken) return false;
        
        try {
            const response = await fetch('/auth/token/refresh/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh: this.refreshToken })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.accessToken = data.access;
                localStorage.setItem('access_token', data.access);
                return true;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
        }
        
        this.logout();
        return false;
    }

    async apiCall(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.accessToken) {
            headers['Authorization'] = `Bearer ${this.accessToken}`;
        }

        const response = await fetch(url, {
            ...options,
            headers
        });

        // Handle token expiration
        if (response.status === 401 && this.accessToken) {
            const refreshed = await this.refreshAccessToken();
            if (refreshed) {
                // Retry the request with new token
                headers['Authorization'] = `Bearer ${this.accessToken}`;
                return fetch(url, { ...options, headers });
            }
        }

        return response;
    }

    setupEventListeners() {
        // Authentication
        document.getElementById('login-form-element').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('register-form-element').addEventListener('submit', (e) => this.handleRegister(e));
        document.getElementById('show-register').addEventListener('click', () => this.showRegisterForm());
        document.getElementById('show-login').addEventListener('click', () => this.showLoginForm());
        document.getElementById('logout-btn').addEventListener('click', () => this.logout());

        // Projects
        document.getElementById('new-project-btn').addEventListener('click', () => this.showProjectModal());
        document.getElementById('import-projects-btn').addEventListener('click', () => this.importExistingProjects());
        document.getElementById('project-form').addEventListener('submit', (e) => this.createProject(e));
        document.getElementById('cancel-project-btn').addEventListener('click', () => this.hideProjectModal());

        // Project actions
        document.getElementById('start-server-btn').addEventListener('click', () => this.startServer());
        document.getElementById('stop-server-btn').addEventListener('click', () => this.stopServer());
        document.getElementById('project-stats-btn').addEventListener('click', () => this.showProjectStats());

        // Chat
        document.getElementById('send-chat-btn').addEventListener('click', () => this.sendChatMessage());
        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendChatMessage();
            }
        });
        
        // Error reporting
        document.getElementById('report-error-btn').addEventListener('click', () => this.showErrorModal());
        document.getElementById('cancel-error-btn').addEventListener('click', () => this.hideErrorModal());
        document.getElementById('error-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitErrorReport();
        });
        
        // Example buttons for quick start
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('example-btn')) {
                const prompt = e.target.dataset.prompt;
                document.getElementById('chat-input').value = prompt;
                document.getElementById('quick-examples').classList.add('hidden');
                this.sendChatMessage();
            }
        });

        // Terminal
        document.getElementById('execute-cmd-btn').addEventListener('click', () => this.executeCommand());
        document.getElementById('command-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.executeCommand();
        });

        // File operations
        document.getElementById('save-file-btn').addEventListener('click', () => this.saveCurrentFile());
        document.getElementById('refresh-files-btn').addEventListener('click', () => this.refreshFiles());
        document.getElementById('refresh-preview-btn').addEventListener('click', () => this.refreshPreview());
    }

    initializeEditor() {
        require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' }});
        require(['vs/editor/editor.main'], () => {
            this.editor = monaco.editor.create(document.getElementById('editor'), {
                value: '# Select a file to edit',
                language: 'python',
                theme: 'vs-dark',
                automaticLayout: true,
                minimap: { enabled: false }
            });
        });
    }

    // Authentication methods
    async handleLogin(e) {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;

        try {
            const response = await fetch('/auth/login/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (response.ok) {
                const data = await response.json();
                this.accessToken = data.tokens.access;
                this.refreshToken = data.tokens.refresh;
                
                localStorage.setItem('access_token', data.tokens.access);
                localStorage.setItem('refresh_token', data.tokens.refresh);
                
                this.showMainApp();
                document.getElementById('user-info').textContent = `Welcome, ${data.user.username}!`;
            } else {
                const error = await response.json();
                alert('Login failed: ' + (error.detail || 'Invalid credentials'));
            }
        } catch (error) {
            alert('Login failed: ' + error.message);
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        const username = document.getElementById('register-username').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        const passwordConfirm = document.getElementById('register-password-confirm').value;

        if (password !== passwordConfirm) {
            alert('Passwords do not match');
            return;
        }

        try {
            const response = await fetch('/auth/register/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    username, 
                    email, 
                    password, 
                    password_confirm: passwordConfirm 
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.accessToken = data.tokens.access;
                this.refreshToken = data.tokens.refresh;
                
                localStorage.setItem('access_token', data.tokens.access);
                localStorage.setItem('refresh_token', data.tokens.refresh);
                
                this.showMainApp();
                document.getElementById('user-info').textContent = `Welcome, ${data.user.username}!`;
            } else {
                const error = await response.json();
                alert('Registration failed: ' + JSON.stringify(error));
            }
        } catch (error) {
            alert('Registration failed: ' + error.message);
        }
    }

    async logout() {
        try {
            if (this.refreshToken) {
                await fetch('/auth/logout/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.accessToken}`
                    },
                    body: JSON.stringify({ refresh: this.refreshToken })
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        }

        this.accessToken = null;
        this.refreshToken = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        this.showLoginModal();
    }

    // UI methods
    showLoginModal() {
        document.getElementById('login-modal').classList.remove('hidden');
        document.getElementById('main-app').classList.add('hidden');
    }

    showMainApp() {
        document.getElementById('login-modal').classList.add('hidden');
        document.getElementById('main-app').classList.remove('hidden');
        this.loadProjects();
    }

    showLoginForm() {
        document.getElementById('login-form').classList.remove('hidden');
        document.getElementById('register-form').classList.add('hidden');
    }

    showRegisterForm() {
        document.getElementById('login-form').classList.add('hidden');
        document.getElementById('register-form').classList.remove('hidden');
    }

    showProjectModal() {
        document.getElementById('project-modal').classList.remove('hidden');
        document.getElementById('project-modal').classList.add('flex');
    }

    hideProjectModal() {
        document.getElementById('project-modal').classList.add('hidden');
        document.getElementById('project-modal').classList.remove('flex');
    }

    // Project methods
    async loadProjects() {
        try {
            // First, try to import any existing projects
            await this.importExistingProjects(false); // false = don't show success message
            
            const response = await this.apiCall('/projects/');
            if (response.ok) {
                const data = await response.json();
                this.renderProjects(data.results || data);
            }
        } catch (error) {
            console.error('Failed to load projects:', error);
        }
    }
    
    async importExistingProjects(showMessage = true) {
        try {
            if (showMessage) {
                this.addToTerminal('Importing existing Django projects...');
            }
            
            const response = await this.apiCall('/projects/import_existing_projects/', {
                method: 'POST'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (showMessage && result.imported_count > 0) {
                    this.addToTerminal(`Successfully imported ${result.imported_count} existing projects!`);
                    // Reload projects to show the imported ones
                    setTimeout(() => this.loadProjects(), 1000);
                } else if (showMessage) {
                    this.addToTerminal('No new projects found to import.');
                }
                return result;
            } else {
                const error = await response.json();
                if (showMessage) {
                    this.addToTerminal(`Failed to import projects: ${error.error || 'Unknown error'}`);
                }
                console.error('Failed to import projects:', error);
            }
        } catch (error) {
            if (showMessage) {
                this.addToTerminal(`Error importing projects: ${error.message}`);
            }
            console.error('Error importing projects:', error);
        }
    }

    renderProjects(projects) {
        const container = document.getElementById('projects-list');
        container.innerHTML = '';

        if (projects.length === 0) {
            container.innerHTML = '<p class="text-gray-500 col-span-full text-center">No projects yet. Create your first project!</p>';
            return;
        }

        projects.forEach(project => {
            const projectCard = document.createElement('div');
            projectCard.className = 'border border-gray-200 rounded-lg p-4 hover:shadow-md cursor-pointer';
            projectCard.innerHTML = `
                <h3 class="font-semibold text-lg mb-2">${project.name}</h3>
                <p class="text-gray-600 text-sm mb-2">${project.description || 'No description'}</p>
                <div class="flex justify-between items-center text-xs text-gray-500">
                    <span>${project.files_count} files</span>
                    <span class="px-2 py-1 rounded ${project.is_running ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">
                        ${project.is_running ? 'Running' : 'Stopped'}
                    </span>
                </div>
            `;
            
            projectCard.addEventListener('click', () => this.selectProject(project));
            container.appendChild(projectCard);
        });
    }

    async createProject(e) {
        e.preventDefault();
        const name = document.getElementById('project-name').value;
        const description = document.getElementById('project-description').value;

        try {
            const response = await this.apiCall('/projects/', {
                method: 'POST',
                body: JSON.stringify({ name, description })
            });

            if (response.ok) {
                const project = await response.json();
                this.hideProjectModal();
                this.selectProject(project);
                this.loadProjects(); // Refresh project list
                this.addToTerminal(`Project "${name}" created successfully!`);
                
                // Clear form
                document.getElementById('project-name').value = '';
                document.getElementById('project-description').value = '';
            } else {
                const error = await response.json();
                alert('Failed to create project: ' + JSON.stringify(error));
            }
        } catch (error) {
            alert('Failed to create project: ' + error.message);
        }
    }

    async selectProject(project) {
        this.currentProject = project;
        document.getElementById('current-project-name').textContent = project.name;
        document.getElementById('project-workspace').classList.remove('hidden');
        
        // Update server button state
        if (project.is_running) {
            document.getElementById('start-server-btn').classList.add('hidden');
            document.getElementById('stop-server-btn').classList.remove('hidden');
            document.getElementById('preview-panel').classList.remove('hidden');
            document.getElementById('app-preview').src = `http://localhost:${project.container_port}`;
        } else {
            document.getElementById('start-server-btn').classList.remove('hidden');
            document.getElementById('stop-server-btn').classList.add('hidden');
            document.getElementById('preview-panel').classList.add('hidden');
        }
        
        // Show/hide quick examples based on project status
        const quickExamples = document.getElementById('quick-examples');
        if (!project.django_project_created) {
            quickExamples.classList.remove('hidden');
        } else {
            quickExamples.classList.add('hidden');
        }
        
        // Update project info panel
        this.updateProjectInfo(project);
        
        await this.loadProjectFiles();
        await this.loadChatMessages();
        
        // Update chat input placeholder based on project status
        this.updateChatPlaceholder();
    }
    
    updateChatPlaceholder() {
        const chatInput = document.getElementById('chat-input');
        const project = this.currentProject;
        
        if (!project) {
            chatInput.placeholder = 'Select a project first...';
            return;
        }
        
        if (!project.django_project_created || project.files_count === 0) {
            chatInput.placeholder = 'Describe what you want to build... (e.g., "Create a fitness tracking app with workouts and progress charts")';
        } else {
            chatInput.placeholder = 'Ask me to modify or enhance your project (e.g., "Add a model to track post views")';
        }
    }
    
    updateProjectInfo(project) {
        const infoPanel = document.getElementById('project-info');
        if (project.project_type || project.key_features || project.complexity_level) {
            infoPanel.classList.remove('hidden');
            document.getElementById('project-type-display').textContent = 
                project.project_type ? project.project_type.replace('_', ' ') : '-';
            document.getElementById('project-features-display').textContent = 
                project.key_features && project.key_features.length > 0 ? 
                project.key_features.slice(0, 3).join(', ') + (project.key_features.length > 3 ? '...' : '') : '-';
            document.getElementById('project-complexity-display').textContent = 
                project.complexity_level || '-';
        } else {
            infoPanel.classList.add('hidden');
        }
    }

    async loadProjectInfo() {
        // Reload project info - this might be called after changes to refresh project data
        if (!this.currentProject) return;
        
        try {
            const response = await this.apiCall(`/projects/${this.currentProject.id}/`);
            if (response.ok) {
                const project = await response.json();
                this.currentProject = project;
                this.updateProjectInfo(project);
            }
        } catch (error) {
            console.error('Failed to load project info:', error);
        }
    }

    async startServer() {
        if (!this.currentProject) return;

        this.addToTerminal('Starting Django development server...');
        
        try {
            const response = await this.apiCall(`/projects/${this.currentProject.id}/start_container/`, {
                method: 'POST'
            });

            if (response.ok) {
                const result = await response.json();
                this.addToTerminal(`🚀 Server started on port ${result.port}`);
                this.addToTerminal(`🔗 Preview URL: http://localhost:${result.port}`);
                this.addToTerminal(`📱 App URL: http://localhost:${result.port}/main/`);
                
                document.getElementById('start-server-btn').classList.add('hidden');
                document.getElementById('stop-server-btn').classList.remove('hidden');
                document.getElementById('preview-panel').classList.remove('hidden');
                
                // Add error handling for iframe
                const iframe = document.getElementById('app-preview');
                const previewUrl = `http://localhost:${result.port}`;
                
                iframe.onload = () => {
                    this.addToTerminal(`✅ Preview loaded successfully at ${previewUrl}`);
                };
                
                iframe.onerror = () => {
                    this.addToTerminal(`❌ Preview failed to load in iframe`);
                    this.addToTerminal(`💡 Opening in new tab: ${previewUrl}/main/`);
                    window.open(`${previewUrl}/main/`, '_blank');
                };
                
                // Add timeout to detect if iframe doesn't load
                setTimeout(() => {
                    try {
                        // Check if iframe loaded content
                        if (!iframe.contentDocument && !iframe.contentWindow) {
                            this.addToTerminal(`⚠️  Iframe blocked by browser or Django`);
                            this.addToTerminal(`🔗 Direct link: ${previewUrl}/main/`);
                            
                            // Add a clickable link in the preview area
                            iframe.style.display = 'none';
                            const previewContainer = iframe.parentElement;
                            const linkDiv = document.createElement('div');
                            linkDiv.className = 'p-4 text-center';
                            linkDiv.innerHTML = `
                                <p class="mb-2">Preview not available in iframe</p>
                                <a href="${previewUrl}/main/" target="_blank" 
                                   class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                                   Open in New Tab
                                </a>
                            `;
                            previewContainer.appendChild(linkDiv);
                        }
                    } catch (e) {
                        // Cross-origin iframe access blocked
                        this.addToTerminal(`🔗 Preview available at: ${previewUrl}/main/`);
                    }
                }, 3000);
                
                iframe.src = previewUrl;
                
                this.currentProject.is_running = true;
                this.currentProject.container_port = result.port;
            } else {
                const error = await response.json();
                this.addToTerminal(`Error: ${error.error || 'Failed to start server'}`);
            }
        } catch (error) {
            this.addToTerminal(`Error: ${error.message}`);
        }
    }

    async stopServer() {
        if (!this.currentProject) return;

        try {
            const response = await this.apiCall(`/projects/${this.currentProject.id}/stop_container/`, {
                method: 'POST'
            });

            if (response.ok) {
                this.addToTerminal('Server stopped');
                
                document.getElementById('start-server-btn').classList.remove('hidden');
                document.getElementById('stop-server-btn').classList.add('hidden');
                document.getElementById('preview-panel').classList.add('hidden');
                
                this.currentProject.is_running = false;
            }
        } catch (error) {
            this.addToTerminal(`Error stopping server: ${error.message}`);
        }
    }

    async showProjectStats() {
        if (!this.currentProject) return;

        try {
            const response = await this.apiCall(`/projects/${this.currentProject.id}/stats/`);
            if (response.ok) {
                const stats = await response.json();
                alert(`Project Stats:
Files: ${stats.files_count}
Total Lines: ${stats.total_lines}
Total Size: ${(stats.total_size / 1024).toFixed(2)} KB
Messages: ${stats.messages_count}
Commands: ${stats.executions_count}
Last Activity: ${new Date(stats.last_activity).toLocaleString()}`);
            }
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    // File operations
    async loadProjectFiles() {
        if (!this.currentProject) return;

        try {
            // Load filesystem files (actual project structure)
            const filesystemResponse = await this.apiCall(`/projects/${this.currentProject.id}/filesystem_files/`);
            
            if (filesystemResponse.ok) {
                const filesystemFiles = await filesystemResponse.json();
                this.renderFileTree(filesystemFiles, 'filesystem');
            }
        } catch (error) {
            console.error('Failed to load filesystem files:', error);
        }
    }

    renderFileTree(files, source = 'database') {
        const container = document.getElementById('file-tree');
        container.innerHTML = '';

        if (files.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-sm">No files yet</p>';
            return;
        }

        // Create header to show file source
        const header = document.createElement('div');
        header.className = 'flex items-center justify-between mb-3 pb-2 border-b border-gray-200';
        header.innerHTML = `
            <span class="text-sm font-medium text-gray-700">
                ${source === 'filesystem' ? '📁 Project Files' : '💾 Database Files'}
            </span>
            <span class="text-xs text-gray-500">${files.length} files</span>
        `;
        container.appendChild(header);

        // Build file tree structure
        const fileTree = this.buildFileTree(files);
        this.renderTreeNode(container, fileTree, 0);
    }

    buildFileTree(files) {
        const tree = {};
        
        files.forEach(file => {
            const parts = file.path.split('/');
            let current = tree;
            
            for (let i = 0; i < parts.length; i++) {
                const part = parts[i];
                
                if (i === parts.length - 1) {
                    // This is a file
                    current[part] = {
                        type: 'file',
                        data: file,
                        icon: this.getFileIcon(file.extension || ''),
                        path: file.path
                    };
                } else {
                    // This is a directory
                    if (!current[part]) {
                        current[part] = {
                            type: 'directory',
                            children: {},
                            icon: '📁',
                            path: parts.slice(0, i + 1).join('/')
                        };
                    }
                    current = current[part].children;
                }
            }
        });
        
        return tree;
    }

    renderTreeNode(container, tree, depth) {
        const indent = depth * 20; // 20px per level
        
        Object.keys(tree).sort().forEach(key => {
            const node = tree[key];
            const nodeElement = document.createElement('div');
            
            if (node.type === 'directory') {
                nodeElement.className = 'flex items-center p-1 hover:bg-gray-50 rounded cursor-pointer';
                nodeElement.style.paddingLeft = `${indent}px`;
                nodeElement.innerHTML = `
                    <span class="text-gray-600 mr-2">${node.icon}</span>
                    <span class="text-sm font-medium text-gray-700">${key}/</span>
                `;
                
                const childrenContainer = document.createElement('div');
                childrenContainer.className = 'ml-4';
                
                // Toggle functionality
                let isExpanded = depth < 2; // Auto-expand first 2 levels
                
                const toggleChildren = () => {
                    isExpanded = !isExpanded;
                    childrenContainer.style.display = isExpanded ? 'block' : 'none';
                    nodeElement.innerHTML = `
                        <span class="text-gray-600 mr-2">${isExpanded ? '📂' : '📁'}</span>
                        <span class="text-sm font-medium text-gray-700">${key}/</span>
                    `;
                };
                
                nodeElement.addEventListener('click', toggleChildren);
                container.appendChild(nodeElement);
                
                // Render children
                this.renderTreeNode(childrenContainer, node.children, depth + 1);
                childrenContainer.style.display = isExpanded ? 'block' : 'none';
                container.appendChild(childrenContainer);
                
            } else {
                // File
                nodeElement.className = 'flex items-center p-1 hover:bg-gray-100 rounded cursor-pointer';
                nodeElement.style.paddingLeft = `${indent}px`;
                nodeElement.innerHTML = `
                    <span class="text-blue-600 mr-2">${node.icon}</span>
                    <span class="text-sm flex-1">${key}</span>
                    <span class="text-xs text-gray-400">${(node.data.size / 1024).toFixed(1)}KB</span>
                `;
                
                nodeElement.addEventListener('click', () => this.selectFilesystemFile(node.data));
                container.appendChild(nodeElement);
            }
        });
    }

    getFileIcon(extension) {
        const iconMap = {
            'py': '🐍',
            'js': '📜',
            'html': '🌐',
            'css': '🎨',
            'json': '📋',
            'md': '📝',
            'txt': '📄',
            'yml': '⚙️',
            'yaml': '⚙️',
            'xml': '📋',
            'sql': '🗃️',
            'sqlite3': '🗄️',
            'png': '🖼️',
            'jpg': '🖼️',
            'jpeg': '🖼️',
            'gif': '🖼️',
            'svg': '🖼️',
            'pdf': '📕',
            'zip': '📦',
            'tar': '📦',
            'gz': '📦',
            'env': '🔐',
            'gitignore': '🚫',
            'dockerfile': '🐳',
            'requirements': '📦'
        };
        
        return iconMap[extension.toLowerCase()] || '📄';
    }

    async selectFilesystemFile(file) {
        this.currentFile = file;
        
        // Update UI
        document.getElementById('current-file-name').textContent = file.path;
        document.getElementById('save-file-btn').disabled = false;
        
        // Load file content from filesystem
        try {
            const response = await this.apiCall(`/projects/${this.currentProject.id}/files/content/?path=${encodeURIComponent(file.path)}`);
            if (response.ok) {
                const data = await response.json();
                this.editor.setValue(data.content || '');
                this.editor.setModel(monaco.editor.createModel(data.content || '', this.getLanguageFromExtension(file.extension)));
            }
        } catch (error) {
            console.error('Failed to load file content:', error);
            // Show placeholder if file can't be loaded
            this.editor.setValue(`// Failed to load file: ${file.path}\n// Error: ${error.message}`);
        }
    }

    getLanguageFromExtension(extension) {
        const languageMap = {
            'py': 'python',
            'js': 'javascript',
            'html': 'html',
            'css': 'css',
            'json': 'json',
            'md': 'markdown',
            'txt': 'plaintext',
            'yml': 'yaml',
            'yaml': 'yaml',
            'xml': 'xml',
            'sql': 'sql',
            'dockerfile': 'dockerfile'
        };
        
        return languageMap[extension.toLowerCase()] || 'plaintext';
    }

    async refreshFiles() {
        const refreshBtn = document.getElementById('refresh-files-btn');
        const originalContent = refreshBtn.textContent;
        
        // Show loading state
        refreshBtn.textContent = '⏳';
        refreshBtn.disabled = true;
        
        try {
            await this.loadProjectFiles();
            this.addToTerminal('🔄 Files refreshed');
        } catch (error) {
            this.addToTerminal('❌ Failed to refresh files');
        } finally {
            // Restore button state
            refreshBtn.textContent = originalContent;
            refreshBtn.disabled = false;
        }
    }

    selectFile(file) {
        this.currentFile = file;
        document.getElementById('current-file-name').textContent = file.path;
        document.getElementById('save-file-btn').disabled = false;

        if (this.editor) {
            const extension = file.path.split('.').pop();
            const languageMap = {
                'py': 'python',
                'html': 'html',
                'css': 'css',
                'js': 'javascript',
                'json': 'json',
                'md': 'markdown'
            };
            
            const language = languageMap[extension] || 'plaintext';
            monaco.editor.setModelLanguage(this.editor.getModel(), language);
            this.editor.setValue(file.content);
        }
    }

    async saveCurrentFile() {
        if (!this.currentFile || !this.editor || !this.currentProject) return;

        const content = this.editor.getValue();
        
        try {
            let response;
            
            if (this.currentFile.id) {
                // Database file - use existing API
                response = await this.apiCall(`/projects/${this.currentProject.id}/files/${this.currentFile.id}/`, {
                    method: 'PATCH',
                    body: JSON.stringify({ content })
                });
            } else {
                // Filesystem file - save to filesystem
                response = await this.apiCall(`/projects/${this.currentProject.id}/save_file/`, {
                    method: 'POST',
                    body: JSON.stringify({ 
                        path: this.currentFile.path,
                        content: content 
                    })
                });
            }

            if (response.ok) {
                this.addToTerminal(`✅ Saved ${this.currentFile.path}`);
                this.currentFile.content = content; // Update local copy
            } else {
                const error = await response.json();
                this.addToTerminal(`❌ Error saving ${this.currentFile.path}: ${error.error || 'Unknown error'}`);
            }
        } catch (error) {
            this.addToTerminal(`❌ Error: ${error.message}`);
        }
    }

    // Chat operations
    async loadChatMessages() {
        if (!this.currentProject) return;

        try {
            // First try to load conversation history (new endpoint)
            const response = await this.apiCall(`/projects/${this.currentProject.id}/conversation_history/`);
            if (response.ok) {
                const result = await response.json();
                this.renderChatMessages(result.messages);
                
                if (result.thread_id) {
                    this.currentProject.thread_id = result.thread_id;
                }
            } else {
                // Fallback to legacy messages endpoint
                const fallbackResponse = await this.apiCall(`/projects/${this.currentProject.id}/messages/`);
                if (fallbackResponse.ok) {
                    const messages = await fallbackResponse.json();
                    this.renderChatMessages(messages);
                }
            }
        } catch (error) {
            console.error('Failed to load chat messages:', error);
        }
    }

    renderChatMessages(messages) {
        const container = document.getElementById('chat-messages');
        container.innerHTML = '';

        if (messages.length === 0) {
            container.innerHTML = '<div class="text-gray-500 text-center text-sm">Ask the AI to help you build your Django application</div>';
            return;
        }

        messages.forEach(message => {
            this.addChatMessage(message.role, message.content);
        });
    }

    addChatMessage(role, content) {
        const container = document.getElementById('chat-messages');
        
        // Clear initial message if present
        if (container.children.length === 1 && container.textContent.includes('Ask the AI')) {
            container.innerHTML = '';
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `mb-3 p-3 rounded-lg text-sm ${
            role === 'user' ? 'bg-blue-100 ml-4' : 'bg-gray-100 mr-4'
        }`;
        
        messageDiv.innerHTML = `
            <div class="font-semibold mb-1">${role === 'user' ? 'You' : 'AI'}:</div>
            <div class="whitespace-pre-wrap">${content}</div>
        `;
        
        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
    }

    async sendChatMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message || !this.currentProject) return;

        this.addChatMessage('user', message);
        input.value = '';

        // Show loading state
        const sendBtn = document.getElementById('send-chat-btn');
        sendBtn.disabled = true;
        sendBtn.textContent = 'Generating...';

        try {
            // Use smart_generate_stream for new projects, conversation_chat for existing projects
            const isNewProject = !this.currentProject.django_project_created || this.currentProject.files_count === 0;
            
            if (isNewProject) {
                // Use streaming for new project generation
                await this.startStreamingGeneration(message);
            } else {
                // Use regular API for existing projects
                const response = await this.apiCall(`/projects/${this.currentProject.id}/conversation_chat/`, {
                    method: 'POST',
                    body: JSON.stringify({ message: message, is_error: false })
                });

                if (response.ok) {
                    const result = await response.json();
                    this.addChatMessage('assistant', result.message);
                    
                    // Handle conversation_chat response (existing projects)
                    if (result.files_modified && result.files_modified.length > 0) {
                        await this.loadProjectFiles();
                        this.addToTerminal(`📝 Files modified: ${result.files_modified.join(', ')}`);
                    }
                    
                    if (result.code_changes && Object.keys(result.code_changes).length > 0) {
                        this.addToTerminal('🔧 Code changes applied:');
                        Object.entries(result.code_changes).forEach(([file, change]) => {
                            this.addToTerminal(`  ${file}: ${change.action}`);
                        });
                    }
                    
                    if (result.suggestions && result.suggestions.length > 0) {
                        this.addToTerminal('💡 Suggestions:');
                        result.suggestions.forEach(suggestion => {
                            this.addToTerminal(`  • ${suggestion}`);
                        });
                    }
                    
                    if (result.error_fixed) {
                        this.addToTerminal('✅ Error has been fixed!');
                    }
                    
                    // Show processing time
                    if (result.processing_time) {
                        this.addToTerminal(`⏱️ Processed in ${result.processing_time.toFixed(2)}s`);
                    }
                    
                    // Update thread ID for context
                    if (result.thread_id) {
                        this.currentProject.thread_id = result.thread_id;
                    }
                } else {
                    const error = await response.json();
                    this.addChatMessage('assistant', `Error: ${error.error || 'Failed to process request'}`);
                    this.addToTerminal(`❌ Error: ${error.error || 'Failed to process request'}`);
                }
            }
        } catch (error) {
            this.addChatMessage('assistant', `Error: ${error.message}`);
            this.addToTerminal(`❌ Error: ${error.message}`);
        } finally {
            const sendBtn = document.getElementById('send-chat-btn');
            sendBtn.disabled = false;
            sendBtn.textContent = 'Send';
        }
    }

    async startStreamingGeneration(message) {
        // Show streaming progress panel
        const streamingProgress = document.getElementById('streaming-progress');
        const progressBar = document.getElementById('streaming-progress-bar');
        const progressText = document.getElementById('streaming-progress-text');
        const statusText = document.getElementById('streaming-status-text');
        const fileFeed = document.getElementById('file-creation-feed');
        
        streamingProgress.classList.remove('hidden');
        progressBar.style.width = '0%';
        progressText.textContent = '0%';
        statusText.textContent = 'Initializing...';
        fileFeed.innerHTML = '';
        
        // Create EventSource for streaming
        const token = this.accessToken;
        const url = `/api/projects/${this.currentProject.id}/smart_generate_stream/?token=${token}&message=${encodeURIComponent(message)}`;
        
        const eventSource = new EventSource(url);
        let lastProgress = 0;
        
        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                switch (data.type) {
                    case 'status':
                        statusText.textContent = data.message;
                        if (data.status === 'initializing') {
                            progressBar.style.width = '10%';
                            progressText.textContent = '10%';
                        }
                        break;
                        
                    case 'file_created':
                        // Update progress
                        if (data.progress) {
                            progressBar.style.width = `${data.progress}%`;
                            progressText.textContent = `${Math.round(data.progress)}%`;
                            lastProgress = data.progress;
                        }
                        
                        // Add file to feed
                        const fileItem = document.createElement('div');
                        fileItem.className = 'file-item creating text-xs text-gray-600 bg-white p-2 rounded border';
                        fileItem.innerHTML = `📄 Created: <span class="font-mono">${data.file}</span>`;
                        fileFeed.appendChild(fileItem);
                        fileFeed.scrollTop = fileFeed.scrollHeight;
                        
                        // Add to terminal
                        this.addToTerminal(`📄 Created: ${data.file}`);
                        break;
                        
                    case 'completion':
                        // Project generation completed
                        progressBar.style.width = '100%';
                        progressText.textContent = '100%';
                        statusText.textContent = 'Project generation completed!';
                        
                        // Add final assistant message
                        if (data.message) {
                            this.addChatMessage('assistant', data.message);
                        }
                        
                        // Update project state
                        if (data.django_project_created) {
                            this.currentProject.django_project_created = true;
                            this.addToTerminal('✅ Complete Django project generated');
                        }
                        
                        // Handle files and reload
                        if (data.files && data.files.length > 0) {
                            this.addToTerminal(`📄 Generated ${data.files.length} file(s)`);
                            setTimeout(() => this.loadProjectFiles(), 1000);
                        }
                        
                        // Show setup commands
                        if (data.commands && data.commands.length > 0) {
                            this.addToTerminal('🔧 Setup commands: ' + data.commands.join(', '));
                        }
                        
                        // Show access URL
                        if (data.access_url) {
                            this.addToTerminal(`🌐 Access URL: ${data.access_url}`);
                        }
                        
                        // Hide streaming panel after a delay
                        setTimeout(() => {
                            streamingProgress.classList.add('hidden');
                        }, 3000);
                        
                        eventSource.close();
                        break;
                        
                    case 'error':
                        statusText.textContent = `Error: ${data.message}`;
                        this.addChatMessage('assistant', `Error: ${data.message}`);
                        this.addToTerminal(`❌ Error: ${data.message}`);
                        eventSource.close();
                        
                        setTimeout(() => {
                            streamingProgress.classList.add('hidden');
                        }, 3000);
                        break;
                        
                    default:
                        console.log('Unknown streaming event:', data);
                }
            } catch (error) {
                console.error('Error parsing streaming data:', error);
            }
        };
        
        eventSource.onerror = (error) => {
            console.error('EventSource error:', error);
            statusText.textContent = 'Streaming connection error';
            eventSource.close();
            
            setTimeout(() => {
                streamingProgress.classList.add('hidden');
            }, 3000);
        };
        
        return new Promise((resolve) => {
            eventSource.addEventListener('completion', () => resolve());
            eventSource.addEventListener('error', () => resolve());
        });
    }

    // Error reporting functionality
    async reportError(errorMessage, errorType = 'runtime_error', errorSource = '') {
        if (!this.currentProject) return;
        
        this.addChatMessage('user', `🚨 ERROR REPORT: ${errorMessage}`);
        
        // Show loading state
        const sendBtn = document.getElementById('send-chat-btn');
        sendBtn.disabled = true;
        sendBtn.textContent = 'Fixing...';
        
        try {
            const response = await this.apiCall(`/projects/${this.currentProject.id}/report_error/`, {
                method: 'POST',
                body: JSON.stringify({
                    error_message: errorMessage,
                    error_type: errorType,
                    error_source: errorSource
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.addChatMessage('assistant', result.message);
                
                // Show files modified
                if (result.files_modified && result.files_modified.length > 0) {
                    await this.loadProjectFiles();
                    this.addToTerminal(`📝 Files modified: ${result.files_modified.join(', ')}`);
                }
                
                // Show if error was fixed
                if (result.error_fixed) {
                    this.addToTerminal('✅ Error has been automatically fixed!');
                }
                
                // Show processing time
                if (result.processing_time) {
                    this.addToTerminal(`⏱️ Fixed in ${result.processing_time.toFixed(2)}s`);
                }
                
            } else {
                const error = await response.json();
                this.addChatMessage('assistant', `Error: ${error.error || 'Failed to process error report'}`);
            }
        } catch (error) {
            console.error('Error reporting failed:', error);
            this.addChatMessage('assistant', `Error: ${error.message}`);
        } finally {
            sendBtn.disabled = false;
            sendBtn.textContent = 'Send';
        }
    }

    // Load conversation history
    async loadConversationHistory() {
        if (!this.currentProject) return;
        
        try {
            const response = await this.apiCall(`/projects/${this.currentProject.id}/conversation_history/`);
            if (response.ok) {
                const result = await response.json();
                this.renderChatMessages(result.messages);
                
                if (result.thread_id) {
                    this.currentProject.thread_id = result.thread_id;
                }
            }
        } catch (error) {
            console.error('Failed to load conversation history:', error);
        }
    }

    // Error reporting modal functions
    showErrorModal() {
        if (!this.currentProject) {
            alert('Please select a project first');
            return;
        }
        document.getElementById('error-modal').classList.remove('hidden');
        document.getElementById('error-modal').classList.add('flex');
        document.getElementById('error-message').focus();
    }

    hideErrorModal() {
        document.getElementById('error-modal').classList.add('hidden');
        document.getElementById('error-modal').classList.remove('flex');
        document.getElementById('error-form').reset();
    }

    async submitErrorReport() {
        const errorMessage = document.getElementById('error-message').value.trim();
        const errorType = document.getElementById('error-type').value;
        const errorSource = document.getElementById('error-source').value.trim();

        if (!errorMessage) {
            alert('Please enter an error message');
            return;
        }

        this.hideErrorModal();
        await this.reportError(errorMessage, errorType, errorSource);
    }

    // Terminal operations
    addToTerminal(message) {
        const terminalOutput = document.getElementById('terminal-output');
        const messageDiv = document.createElement('div');
        messageDiv.textContent = message;
        messageDiv.className = 'text-green-400';
        terminalOutput.appendChild(messageDiv);
        
        // Auto-scroll to bottom
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    }

    async executeCommand() {
        const input = document.getElementById('command-input');
        const command = input.value.trim();
        
        if (!command || !this.currentProject) return;

        this.addToTerminal(`Executing: ${command}`);
        input.value = '';

        const executeBtn = document.getElementById('execute-cmd-btn');
        executeBtn.disabled = true;
        executeBtn.textContent = 'Running...';

        try {
            const response = await this.apiCall(`/projects/${this.currentProject.id}/execute_command/`, {
                method: 'POST',
                body: JSON.stringify({ command })
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.addToTerminal(result.output || 'Command completed successfully');
                } else {
                    this.addToTerminal(`Error: ${result.error || 'Command failed'}`);
                    if (result.error_output) {
                        this.addToTerminal(result.error_output);
                    }
                }
            } else {
                const error = await response.json();
                this.addToTerminal(`Error: ${error.detail || 'Failed to execute command'}`);
            }
        } catch (error) {
            this.addToTerminal(`Error: ${error.message}`);
        } finally {
            executeBtn.disabled = false;
            executeBtn.textContent = 'Execute';
        }
    }

    addToTerminal(message) {
        const terminal = document.getElementById('terminal-output');
        const line = document.createElement('div');
        line.className = 'mb-1';
        line.textContent = `$ ${message}`;
        terminal.appendChild(line);
        terminal.scrollTop = terminal.scrollHeight;
    }

    refreshPreview() {
        const iframe = document.getElementById('app-preview');
        iframe.src = iframe.src;
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DjangoAIBuilder();
});