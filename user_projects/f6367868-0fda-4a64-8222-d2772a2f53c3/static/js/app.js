// Main application JavaScript
const BoutiqueApp = {
    init: function() {
        this.initWebSocket();
        this.setupEventListeners();
        this.initCart();
        this.initSearch();
        this.setupFilters();
        this.initWishlist();
        this.initRatings();
        this.setupPayments();
    },

    csrfToken: document.querySelector('[name=csrfmiddlewaretoken]')?.value,

    initWebSocket: function() {
        const ws = new WebSocket(`ws://${window.location.host}/ws/boutique/`);
        ws.onmessage = function(e) {
            const data = JSON.parse(e.data);
            if (data.type === 'inventory_update') {
                BoutiqueApp.updateInventory(data.product_id, data.quantity);
            }
        };
    },

    setupEventListeners: function() {
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeTooltips();
            this.setupModalHandlers();
            this.initQuantityControls();
        });
    },

    initCart: function() {
        const cart = {
            items: JSON.parse(localStorage.getItem('cart') || '[]'),
            
            addItem: function(productId, quantity) {
                const existingItem = this.items.find(item => item.id === productId);
                if (existingItem) {
                    existingItem.quantity += quantity;
                } else {
                    this.items.push({ id: productId, quantity: quantity });
                }
                this.saveCart();
                this.updateCartUI();
            },

            removeItem: function(productId) {
                this.items = this.items.filter(item => item.id !== productId);
                this.saveCart();
                this.updateCartUI();
            },

            saveCart: function() {
                localStorage.setItem('cart', JSON.stringify(this.items));
            },

            updateCartUI: function() {
                const cartCount = document.getElementById('cart-count');
                if (cartCount) {
                    cartCount.textContent = this.items.reduce((acc, item) => acc + item.quantity, 0);
                }
            }
        };

        window.BoutiqueCart = cart;
    },

    initSearch: function() {
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            let timeout = null;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.performSearch(e.target.value);
                }, 500);
            });
        }
    },

    performSearch: function(query) {
        fetch(`/api/search/?q=${encodeURIComponent(query)}`, {
            headers: {
                'X-CSRFToken': this.csrfToken
            }
        })
        .then(response => response.json())
        .then(data => this.updateSearchResults(data));
    },

    setupFilters: function() {
        const filterForms = document.querySelectorAll('.filter-form');
        filterForms.forEach(form => {
            form.addEventListener('change', () => {
                const formData = new FormData(form);
                this.applyFilters(formData);
            });
        });
    },

    initWishlist: function() {
        const wishlistButtons = document.querySelectorAll('.wishlist-btn');
        wishlistButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const productId = btn.dataset.productId;
                this.toggleWishlist(productId);
            });
        });
    },

    initRatings: function() {
        const ratingStars = document.querySelectorAll('.rating-star');
        ratingStars.forEach(star => {
            star.addEventListener('click', (e) => {
                const rating = e.target.dataset.rating;
                const productId = e.target.closest('.rating-container').dataset.productId;
                this.submitRating(productId, rating);
            });
        });
    },

    setupPayments: function() {
        if (typeof Stripe !== 'undefined') {
            const stripe = Stripe('your-publishable-key');
            const elements = stripe.elements();
            const card = elements.create('card');
            card.mount('#card-element');

            const form = document.getElementById('payment-form');
            if (form) {
                form.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const {token, error} = await stripe.createToken(card);
                    if (error) {
                        this.showError(error.message);
                    } else {
                        this.processPayment(token);
                    }
                });
            }
        }
    },

    // Form validation
    validateForm: function(form) {
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!input.value.trim()) {
                this.showError(`${input.name} is required`);
                isValid = false;
            }
        });

        return isValid;
    },

    // UI Helpers
    showError: function(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger';
        errorDiv.textContent = message;
        document.querySelector('.messages-container').appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 5000);
    },

    showSuccess: function(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'alert alert-success';
        successDiv.textContent = message;
        document.querySelector('.messages-container').appendChild(successDiv);
        setTimeout(() => successDiv.remove(), 5000);
    },

    initializeTooltips: function() {
        const tooltips = document.querySelectorAll('[data-toggle="tooltip"]');
        tooltips.forEach(tooltip => {
            new bootstrap.Tooltip(tooltip);
        });
    },

    initQuantityControls: function() {
        const quantityControls = document.querySelectorAll('.quantity-control');
        quantityControls.forEach(control => {
            const input = control.querySelector('input');
            const increment = control.querySelector('.increment');
            const decrement = control.querySelector('.decrement');

            increment?.addEventListener('click', () => {
                input.value = parseInt(input.value) + 1;
                input.dispatchEvent(new Event('change'));
            });

            decrement?.addEventListener('click', () => {
                if (parseInt(input.value) > 1) {
                    input.value = parseInt(input.value) - 1;
                    input.dispatchEvent(new Event('change'));
                }
            });
        });
    },

    updateInventory: function(productId, quantity) {
        const inventoryElement = document.querySelector(`[data-inventory-id="${productId}"]`);
        if (inventoryElement) {
            inventoryElement.textContent = quantity;
            if (quantity < 5) {
                inventoryElement.classList.add('low-stock');
            }
        }
    }
};

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    BoutiqueApp.init();
});

// Social login handlers
function handleGoogleLogin() {
    window.location.href = '/auth/google/login/';
}

function handleFacebookLogin() {
    window.location.href = '/auth/facebook/login/';
}

// Mobile responsiveness
window.addEventListener('resize', () => {
    const width = window.innerWidth;
    if (width < 768) {
        document.body.classList.add('mobile-view');
    } else {
        document.body.classList.remove('mobile-view');
    }
});