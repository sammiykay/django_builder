class CommentSystem {
    constructor() {
        this.replyForms = {};
    }

    showReplyForm(commentId) {
        if (!this.replyForms[commentId]) {
            const form = $(`#reply-template`).clone();
            form.attr('id', `reply-form-${commentId}`);
            $(`#comment-${commentId}`).append(form);
            this.replyForms[commentId] = form;
        }
        this.replyForms[commentId].toggle();
    }

    submitReply(commentId) {
        const content = $(`#reply-form-${commentId} textarea`).val();
        $.ajax({
            url: '/api/comments/create/',
            type: 'POST',
            data: {
                parent_id: commentId,
                content: content
            },
            success: function(response) {
                location.reload();
            }
        });
    }
}

// Tag System
function initializeTagSystem() {
    $('.tag-cloud').on('click', '.tag', function() {
        const tag = $(this).data('tag');
        filterPostsByTag(tag);
    });
}

function filterPostsByTag(tag) {
    $.get(`/api/posts/filter/?tag=${tag}`, function(response) {
        $('#posts-container').html(response.posts);
    });
}

// Search Functionality
let searchTimeout;
$('#search-input').on('input', function() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        const query = $(this).val();
        if (query.length > 2) {
            $.get(`/api/search/?q=${query}`, function(response) {
                $('#search-results').html(response.results);
            });
        }
    }, 300);
});

// Image Upload and Preview
function handleImageUpload(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            $('#image-preview').attr('src', e.target.result);
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Form Validation
function validatePostForm() {
    const title = $('#post-title').val();
    const content = editor.root.innerHTML;
    
    if (!title.trim()) {
        showError('Title is required');
        return false;
    }
    
    if (content.trim() === '<p><br></p>') {
        showError('Content is required');
        return false;
    }
    
    return true;
}

function showError(message) {
    const errorDiv = $('<div>').addClass('alert alert-danger').text(message);
    $('#form-errors').html(errorDiv);
}

// Reading Time Estimation
function calculateReadingTime(content) {
    const wordsPerMinute = 200;
    const wordCount = content.trim().split(/\s+/).length;
    const readingTime = Math.ceil(wordCount / wordsPerMinute);
    $('#reading-time').text(`${readingTime} min read`);
}

// Notification System
function initializeNotifications() {
    setInterval(checkNewNotifications, 30000);
}

function checkNewNotifications() {
    $.get('/api/notifications/check/', function(response) {
        if (response.count > 0) {
            $('#notification-badge').text(response.count).show();
        }
    });
}

// Social Share Buttons
function sharePost(platform, url, title) {
    const shareUrls = {
        twitter: `https://twitter.com/intent/tweet?url=${url}&text=${title}`,
        facebook: `https://www.facebook.com/sharer/sharer.php?u=${url}`,
        linkedin: `https://www.linkedin.com/shareArticle?url=${url}&title=${title}`
    };
    
    window.open(shareUrls[platform], '_blank', 'width=600,height=400');
}

// Initialize everything when document is ready
$(document).ready(function() {
    initializeTagSystem();
    initializeNotifications();
    
    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();
    
    // Handle post scheduling
    $('#schedule-post').daterangepicker({
        singleDatePicker: true,
        timePicker: true,
        locale: {
            format: 'YYYY-MM-DD HH:mm'
        }
    });
    
    // Comment moderation
    $('.moderate-comment').click(function() {
        const commentId = $(this).data('comment-id');
        const action = $(this).data('action');
        
        $.post(`/api/comments/${commentId}/moderate/`, {
            action: action
        }, function() {
            location.reload();
        });
    });
});