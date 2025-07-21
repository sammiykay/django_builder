// Main application JavaScript
const SocialSphere = {
    init() {
        this.setupWebSocket();
        this.initializeUI();
        this.bindEvents();
        this.setupInfiniteScroll();
        this.initializeRichTextEditor();
        this.initializeImageCropper();
    },

    csrfToken: document.querySelector('[name=csrfmiddlewaretoken]')?.value,

    setupWebSocket() {
        const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
        this.socket = new WebSocket(`${ws_scheme}://${window.location.host}/ws/notifications/`);
        
        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleNotification(data);
        };
    },

    handleNotification(data) {
        const notification = `
            <div class="notification" data-id="${data.id}">
                <p>${data.message}</p>
                <small>${data.timestamp}</small>
            </div>
        `;
        document.getElementById('notifications-container').insertAdjacentHTML('afterbegin', notification);
    },

    initializeUI() {
        // Rich text editor initialization
        if (document.getElementById('post-editor')) {
            tinymce.init({
                selector: '#post-editor',
                plugins: 'link image media mention hashtag',
                toolbar: 'bold italic | link image | mention hashtag',
                mentions: {
                    source: this.fetchUserMentions
                }
            });
        }

        // Image cropper initialization
        if (document.getElementById('avatar-upload')) {
            const cropper = new Cropper(document.getElementById('avatar-preview'), {
                aspectRatio: 1,
                viewMode: 1,
            });
        }
    },

    bindEvents() {
        // Like/Unlike posts
        document.addEventListener('click', (e) => {
            if (e.target.matches('.like-button')) {
                this.handleLike(e);
            }
        });

        // Comment threading
        document.addEventListener('click', (e) => {
            if (e.target.matches('.reply-button')) {
                this.showReplyForm(e);
            }
        });

        // Bookmark posts
        document.addEventListener('click', (e) => {
            if (e.target.matches('.bookmark-button')) {
                this.toggleBookmark(e);
            }
        });

        // Search functionality
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(this.handleSearch, 300));
        }
    },

    setupInfiniteScroll() {
        const feedContainer = document.querySelector('.feed-container');
        if (!feedContainer) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadMorePosts();
                }
            });
        });

        observer.observe(document.querySelector('.load-more-trigger'));
    },

    async handleLike(e) {
        e.preventDefault();
        const postId = e.target.dataset.postId;
        
        try {
            const response = await fetch(`/api/posts/${postId}/like/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                e.target.classList.toggle('liked');
                const likeCount = e.target.querySelector('.like-count');
                const data = await response.json();
                likeCount.textContent = data.likes;
            }
        } catch (error) {
            console.error('Error liking post:', error);
        }
    },

    async loadMorePosts() {
        const lastPost = document.querySelector('.post:last-child');
        const lastPostId = lastPost?.dataset.postId;

        try {
            const response = await fetch(`/api/posts/feed/?last_post=${lastPostId}`);
            const data = await response.json();
            
            data.posts.forEach(post => {
                const postElement = this.createPostElement(post);
                document.querySelector('.feed-container').appendChild(postElement);
            });
        } catch (error) {
            console.error('Error loading more posts:', error);
        }
    },

    async handleSearch(e) {
        const query = e.target.value;
        if (query.length < 2) return;

        try {
            const response = await fetch(`/api/search/?q=${encodeURIComponent(query)}`);
            const results = await response.json();
            this.displaySearchResults(results);
        } catch (error) {
            console.error('Error searching:', error);
        }
    },

    displaySearchResults(results) {
        const container = document.getElementById('search-results');
        container.innerHTML = '';
        
        results.forEach(result => {
            container.insertAdjacentHTML('beforeend', `
                <div class="search-result">
                    <a href="${result.url}">${result.title}</a>
                    <p>${result.excerpt}</p>
                </div>
            `);
        });
    },

    async fetchUserMentions(query) {
        try {
            const response = await fetch(`/api/users/mentions/?q=${encodeURIComponent(query)}`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching mentions:', error);
            return [];
        }
    },

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Form validation
    validateForm(formElement) {
        const inputs = formElement.querySelectorAll('input, textarea');
        let isValid = true;

        inputs.forEach(input => {
            if (input.hasAttribute('required') && !input.value.trim()) {
                input.classList.add('error');
                isValid = false;
            } else {
                input.classList.remove('error');
            }

            if (input.type === 'email' && input.value) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(input.value)) {
                    input.classList.add('error');
                    isValid = false;
                }
            }
        });

        return isValid;
    },

    createPostElement(post) {
        const template = document.createElement('div');
        template.className = 'post';
        template.dataset.postId = post.id;
        template.innerHTML = `
            <div class="post-header">
                <img src="${post.author.avatar}" alt="${post.author.name}" class="avatar">
                <h3>${post.author.name}</h3>
            </div>
            <div class="post-content">${post.content}</div>
            <div class="post-actions">
                <button class="like-button ${post.liked ? 'liked' : ''}" data-post-id="${post.id}">
                    <span class="like-count">${post.likes}</span>
                </button>
                <button class="comment-button">Comment</button>
                <button class="share-button">Share</button>
                <button class="bookmark-button ${post.bookmarked ? 'bookmarked' : ''}">Bookmark</button>
            </div>
        `;
        return template;
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    SocialSphere.init();
});

// Handle file uploads
const FileUploader = {
    init() {
        this.bindEvents();
    },

    bindEvents() {
        const fileInputs = document.querySelectorAll('input[type="file"]');
        fileInputs.forEach(input => {
            input.addEventListener('change', this.handleFileSelect.bind(this));
        });
    },

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'video/mp4'];
        
        files.forEach(file => {
            if (allowedTypes.includes(file.type)) {
                this.uploadFile(file);
            } else {
                alert('Invalid file type. Please upload images or videos only.');
            }
        });
    },

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('csrfmiddlewaretoken', SocialSphere.csrfToken);

        try {
            const response = await fetch('/api/upload/', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                this.handleUploadSuccess(data);
            }
        } catch (error) {
            console.error('Error uploading file:', error);
        }
    },

    handleUploadSuccess(data) {
        const preview = document.createElement('div');
        preview.className = 'upload-preview';
        preview.innerHTML = `
            <img src="${data.url}" alt="Upload preview">
            <button class="remove-upload" data-id="${data.id}">Remove</button>
        `;
        document.querySelector('.uploads-container').appendChild(preview);
    }
};

FileUploader.init();