// Landing Page Interactive JavaScript
document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // Configuration
    const config = {
        scrollOffset: 80,
        animationDuration: 300,
        throttleDelay: 16,
        intersectionThreshold: 0.1,
        parallaxSpeed: 0.5
    };

    // Utility Functions
    const utils = {
        // Throttle function for performance optimization
        throttle: function(func, delay) {
            let timeoutId;
            let lastExecTime = 0;
            return function(...args) {
                const currentTime = Date.now();
                if (currentTime - lastExecTime > delay) {
                    func.apply(this, args);
                    lastExecTime = currentTime;
                } else {
                    clearTimeout(timeoutId);
                    timeoutId = setTimeout(() => {
                        func.apply(this, args);
                        lastExecTime = Date.now();
                    }, delay - (currentTime - lastExecTime));
                }
            };
        },

        // Debounce function
        debounce: function(func, delay) {
            let timeoutId;
            return function(...args) {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => func.apply(this, args), delay);
            };
        },

        // Smooth scroll to target
        smoothScrollTo: function(target) {
            const targetElement = document.querySelector(target);
            if (targetElement) {
                const targetPosition = targetElement.offsetTop - config.scrollOffset;
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        },

        // Check if element is in viewport
        isInViewport: function(element, threshold = config.intersectionThreshold) {
            const rect = element.getBoundingClientRect();
            const windowHeight = window.innerHeight || document.documentElement.clientHeight;
            const windowWidth = window.innerWidth || document.documentElement.clientWidth;

            return (
                rect.top >= -threshold * windowHeight &&
                rect.left >= -threshold * windowWidth &&
                rect.bottom <= windowHeight + threshold * windowHeight &&
                rect.right <= windowWidth + threshold * windowWidth
            );
        },

        // Get scroll position
        getScrollPosition: function() {
            return window.pageYOffset || document.documentElement.scrollTop;
        }
    };

    // Navigation functionality
    const navigation = {
        navbar: document.getElementById('navbar'),
        navMenu: document.getElementById('nav-menu'),
        hamburger: document.getElementById('hamburger'),
        navLinks: document.querySelectorAll('.nav-link'),

        init: function() {
            this.bindEvents();
            this.updateActiveLink();
        },

        bindEvents: function() {
            // Hamburger menu toggle
            if (this.hamburger) {
                this.hamburger.addEventListener('click', this.toggleMobileMenu.bind(this));
            }

            // Navigation links smooth scroll
            this.navLinks.forEach(link => {
                link.addEventListener('click', this.handleNavClick.bind(this));
            });

            // Close mobile menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!this.navbar.contains(e.target) && this.navMenu.classList.contains('active')) {
                    this.closeMobileMenu();
                }
            });

            // Handle scroll for navbar styles and active link
            window.addEventListener('scroll', utils.throttle(() => {
                this.updateNavbarStyle();
                this.updateActiveLink();
            }, config.throttleDelay));

            // Handle resize
            window.addEventListener('resize', utils.debounce(() => {
                if (window.innerWidth > 768 && this.navMenu.classList.contains('active')) {
                    this.closeMobileMenu();
                }
            }, 250));
        },

        toggleMobileMenu: function() {
            this.hamburger.classList.toggle('active');
            this.navMenu.classList.toggle('active');
            
            // Prevent body scroll when menu is open
            document.body.style.overflow = this.navMenu.classList.contains('active') ? 'hidden' : '';
        },

        closeMobileMenu: function() {
            this.hamburger.classList.remove('active');
            this.navMenu.classList.remove('active');
            document.body.style.overflow = '';
        },

        handleNavClick: function(e) {
            e.preventDefault();
            const target = e.target.getAttribute('href');
            
            if (target && target.startsWith('#')) {
                utils.smoothScrollTo(target);
                this.closeMobileMenu();
            }
        },

        updateNavbarStyle: function() {
            const scrollPosition = utils.getScrollPosition();
            
            if (scrollPosition > 50) {
                this.navbar.classList.add('scrolled');
            } else {
                this.navbar.classList.remove('scrolled');
            }
        },

        updateActiveLink: function() {
            const scrollPosition = utils.getScrollPosition() + config.scrollOffset + 50;
            const sections = document.querySelectorAll('section[id]');
            
            let activeSection = '';
            
            sections.forEach(section => {
                const sectionTop = section.offsetTop;
                const sectionBottom = sectionTop + section.offsetHeight;
                
                if (scrollPosition >= sectionTop && scrollPosition <= sectionBottom) {
                    activeSection = section.getAttribute('id');
                }
            });

            // Update active nav link
            this.navLinks.forEach(link => {
                const href = link.getAttribute('href');
                if (href === `#${activeSection}`) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            });
        }
    };

    // Scroll animations and parallax effects
    const scrollAnimations = {
        elements: {
            fadeInElements: document.querySelectorAll('.fade-in-up'),
            scrollRevealElements: document.querySelectorAll('.scroll-reveal'),
            parallaxElements: document.querySelectorAll('.gradient-orb'),
            codePreview: document.querySelector('.code-preview'),
            statsNumbers: document.querySelectorAll('.stat-number')
        },

        observer: null,
        animatedElements: new Set(),

        init: function() {
            this.setupIntersectionObserver();
            this.bindScrollEvents();
            this.initCounters();
        },

        setupIntersectionObserver: function() {
            const options = {
                threshold: config.intersectionThreshold,
                rootMargin: '50px 0px -50px 0px'
            };

            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && !this.animatedElements.has(entry.target)) {
                        this.animateElement(entry.target);
                        this.animatedElements.add(entry.target);
                    }
                });
            }, options);

            // Observe scroll reveal elements
            this.elements.scrollRevealElements.forEach(element => {
                this.observer.observe(element);
            });

            // Observe stats for counter animation
            this.elements.statsNumbers.forEach(element => {
                this.observer.observe(element);
            });
        },

        bindScrollEvents: function() {
            window.addEventListener('scroll', utils.throttle(() => {
                this.updateParallaxElements();
                this.updateCodePreview();
            }, config.throttleDelay));
        },

        animateElement: function(element) {
            if (element.classList.contains('scroll-reveal')) {
                element.classList.add('revealed');
            }
            
            if (element.classList.contains('stat-number')) {
                this.animateCounter(element);
            }
        },

        updateParallaxElements: function() {
            const scrolled = utils.getScrollPosition();
            
            this.elements.parallaxElements.forEach((element, index) => {
                const rate = scrolled * (config.parallaxSpeed + index * 0.1);
                element.style.transform = `translateY(${rate}px)`;
            });
        },

        updateCodePreview: function() {
            if (!this.elements.codePreview) return;
            
            const rect = this.elements.codePreview.getBoundingClientRect();
            const isVisible = rect.top < window.innerHeight && rect.bottom > 0;
            
            if (isVisible) {
                const scrollProgress = Math.min(1, Math.max(0, 
                    (window.innerHeight - rect.top) / window.innerHeight
                ));
                
                // Add subtle floating animation
                const float = Math.sin(Date.now() * 0.001) * 5;
                this.elements.codePreview.style.transform = `translateY(${float}px) scale(${0.95 + scrollProgress * 0.05})`;
            }
        },

        animateCounter: function(element) {
            const target = parseInt(element.textContent.replace(/[^\d]/g, ''));
            const suffix = element.textContent.replace(/[\d\s]/g, '');
            let current = 0;
            const increment = target / 60; // Animate over ~1 second at 60fps
            
            const updateCounter = () => {
                current += increment;
                if (current < target) {
                    element.textContent = Math.floor(current) + suffix;
                    requestAnimationFrame(updateCounter);
                } else {
                    element.textContent = target + suffix;
                }
            };
            
            updateCounter();
        },

        initCounters: function() {
            // Initialize counter values to 0
            this.elements.statsNumbers.forEach(element => {
                const originalText = element.textContent;
                element.setAttribute('data-target', originalText);
                const suffix = originalText.replace(/[\d\s]/g, '');
                element.textContent = '0' + suffix;
            });
        }
    };

    // Interactive features and micro-interactions
    const interactions = {
        elements: {
            buttons: document.querySelectorAll('.btn'),
            featureCards: document.querySelectorAll('.feature-card'),
            codeLines: document.querySelectorAll('.code-line'),
            contactForm: document.querySelector('.contact-form')
        },

        init: function() {
            this.setupButtonEffects();
            this.setupCardEffects();
            this.setupCodeAnimation();
            this.setupFormHandling();
            this.setupKeyboardNavigation();
        },

        setupButtonEffects: function() {
            this.elements.buttons.forEach(button => {
                // Ripple effect on click
                button.addEventListener('click', this.createRippleEffect.bind(this));
                
                // Enhanced hover effects
                button.addEventListener('mouseenter', (e) => {
                    if (button.classList.contains('btn-primary')) {
                        button.style.filter = 'brightness(1.1) saturate(1.1)';
                    }
                });
                
                button.addEventListener('mouseleave', (e) => {
                    button.style.filter = '';
                });
            });
        },

        createRippleEffect: function(e) {
            const button = e.currentTarget;
            const rect = button.getBoundingClientRect();
            const ripple = document.createElement('span');
            
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                pointer-events: none;
                transform: scale(0);
                animation: ripple 0.6s ease-out;
            `;
            
            button.style.position = 'relative';
            button.style.overflow = 'hidden';
            button.appendChild(ripple);
            
            // Remove ripple after animation
            setTimeout(() => {
                if (ripple.parentNode) {
                    ripple.parentNode.removeChild(ripple);
                }
            }, 600);
        },

        setupCardEffects: function() {
            this.elements.featureCards.forEach(card => {
                card.addEventListener('mouseenter', (e) => {
                    // Add subtle scale and rotation
                    card.style.transform = 'translateY(-5px) scale(1.02)';
                });
                
                card.addEventListener('mouseleave', (e) => {
                    card.style.transform = '';
                });
                
                // Add tilt effect based on mouse position
                card.addEventListener('mousemove', (e) => {
                    const rect = card.getBoundingClientRect();
                    const centerX = rect.left + rect.width / 2;
                    const centerY = rect.top + rect.height / 2;
                    const mouseX = e.clientX;
                    const mouseY = e.clientY;
                    
                    const rotateX = (mouseY - centerY) / 10;
                    const rotateY = (centerX - mouseX) / 10;
                    
                    card.style.transform = `translateY(-5px) scale(1.02) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
                });
            });
        },

        setupCodeAnimation: function() {
            let animationTimeout;
            
            const animateTyping = () => {
                const typingLine = document.querySelector('.typing-animation');
                if (typingLine) {
                    typingLine.style.animation = 'none';
                    setTimeout(() => {
                        typingLine.style.animation = 'typing 3s steps(40) infinite';
                    }, 100);
                }
            };
            
            // Start animation when code preview is visible
            const codePreview = document.querySelector('.code-preview');
            if (codePreview && window.IntersectionObserver) {
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            animateTyping();
                            clearTimeout(animationTimeout);
                            animationTimeout = setInterval(animateTyping, 4000);
                        } else {
                            clearTimeout(animationTimeout);
                        }
                    });
                });
                
                observer.observe(codePreview);
            }
        },

        setupFormHandling: function() {
            if (!this.elements.contactForm) return;
            
            const form = this.elements.contactForm;
            const inputs = form.querySelectorAll('input, textarea');
            
            // Enhanced form validation and feedback
            inputs.forEach(input => {
                input.addEventListener('focus', (e) => {
                    e.target.parentElement.classList.add('focused');
                });
                
                input.addEventListener('blur', (e) => {
                    e.target.parentElement.classList.remove('focused');
                    this.validateField(e.target);
                });
                
                input.addEventListener('input', (e) => {
                    this.clearFieldError(e.target);
                });
            });
            
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleFormSubmit(form);
            });
        },

        validateField: function(field) {
            const value = field.value.trim();
            let isValid = true;
            
            if (field.hasAttribute('required') && !value) {
                isValid = false;
                this.showFieldError(field, 'This field is required');
            } else if (field.type === 'email' && value && !this.isValidEmail(value)) {
                isValid = false;
                this.showFieldError(field, 'Please enter a valid email address');
            }
            
            return isValid;
        },

        showFieldError: function(field, message) {
            this.clearFieldError(field);
            
            const errorElement = document.createElement('span');
            errorElement.className = 'field-error';
            errorElement.textContent = message;
            errorElement.style.cssText = `
                color: #fc8181;
                font-size: 0.875rem;
                margin-top: 0.25rem;
                display: block;
            `;
            
            field.parentElement.appendChild(errorElement);
            field.style.borderColor = '#fc8181';
        },

        clearFieldError: function(field) {
            const errorElement = field.parentElement.querySelector('.field-error');
            if (errorElement) {
                errorElement.remove();
            }
            field.style.borderColor = '';
        },

        isValidEmail: function(email) {
            return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
        },

        handleFormSubmit: function(form) {
            const formData = new FormData(form);
            let isFormValid = true;
            
            // Validate all fields
            form.querySelectorAll('input, textarea').forEach(field => {
                if (!this.validateField(field)) {
                    isFormValid = false;
                }
            });
            
            if (isFormValid) {
                this.submitForm(formData);
            }
        },

        submitForm: function(formData) {
            const submitButton = this.elements.contactForm.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;
            
            // Show loading state
            submitButton.textContent = 'Sending...';
            submitButton.disabled = true;
            
            // Simulate form submission (replace with actual API call)
            setTimeout(() => {
                this.showFormSuccess();
                submitButton.textContent = originalText;
                submitButton.disabled = false;
                this.elements.contactForm.reset();
            }, 2000);
        },

        showFormSuccess: function() {
            const successMessage = document.createElement('div');
            successMessage.className = 'form-success';
            successMessage.textContent = 'Thank you! Your message has been sent successfully.';
            successMessage.style.cssText = `
                background: #48bb78;
                color: white;
                padding: 1rem;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
                opacity: 0;
                transition: opacity 0.3s ease;
            `;
            
            this.elements.contactForm.insertBefore(successMessage, this.elements.contactForm.firstChild);
            
            setTimeout(() => {
                successMessage.style.opacity = '1';
            }, 100);
            
            setTimeout(() => {
                successMessage.style.opacity = '0';
                setTimeout(() => {
                    if (successMessage.parentNode) {
                        successMessage.parentNode.removeChild(successMessage);
                    }
                }, 300);
            }, 5000);
        },

        setupKeyboardNavigation: function() {
            // Enhanced keyboard navigation for accessibility
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    navigation.closeMobileMenu();
                }
            });
            
            // Focus management for mobile menu
            navigation.navLinks.forEach((link, index) => {
                link.addEventListener('keydown', (e) => {
                    if (e.key === 'ArrowDown') {
                        e.preventDefault();
                        const nextLink = navigation.navLinks[index + 1] || navigation.navLinks[0];
                        nextLink.focus();
                    } else if (e.key === 'ArrowUp') {
                        e.preventDefault();
                        const prevLink = navigation.navLinks[index - 1] || navigation.navLinks[navigation.navLinks.length - 1];
                        prevLink.focus();
                    }
                });
            });
        }
    };

    // Performance optimization
    const performance = {
        init: function() {
            this.setupImageLazyLoading();
            this.optimizeAnimations();
            this.setupPrefetching();
        },

        setupImageLazyLoading: function() {
            // Implement intersection observer for lazy loading images if needed
            const images = document.querySelectorAll('img[data-src]');
            
            if (images.length > 0 && 'IntersectionObserver' in window) {
                const imageObserver = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            img.src = img.dataset.src;
                            img.classList.remove('lazy');
                            imageObserver.unobserve(img);
                        }
                    });
                });
                
                images.forEach(img => imageObserver.observe(img));
            }
        },

        optimizeAnimations: function() {
            // Pause animations when tab is not visible
            document.addEventListener('visibilitychange', () => {
                const animations = document.querySelectorAll('.gradient-orb, .loading-bars, .container-icon');
                
                animations.forEach(element => {
                    if (document.hidden) {
                        element.style.animationPlayState = 'paused';
                    } else {
                        element.style.animationPlayState = 'running';
                    }
                });
            });
        },

        setupPrefetching: function() {
            // Prefetch resources on hover for better perceived performance
            const prefetchableLinks = document.querySelectorAll('a[href^="#"]');
            
            prefetchableLinks.forEach(link => {
                link.addEventListener('mouseenter', () => {
                    const target = link.getAttribute('href');
                    if (target && target.startsWith('#')) {
                        const targetElement = document.querySelector(target);
                        if (targetElement) {
                            // Preload target section content
                            targetElement.style.willChange = 'transform, opacity';
                        }
                    }
                });
                
                link.addEventListener('mouseleave', () => {
                    const target = link.getAttribute('href');
                    if (target && target.startsWith('#')) {
                        const targetElement = document.querySelector(target);
                        if (targetElement) {
                            targetElement.style.willChange = 'auto';
                        }
                    }
                });
            });
        }
    };

    // Initialize all modules
    navigation.init();
    scrollAnimations.init();
    interactions.init();
    performance.init();

    // Add CSS for ripple animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple {
            to {
                transform: scale(2);
                opacity: 0;
            }
        }
        
        @keyframes typing {
            0% { width: 0; }
            50% { width: 100%; }
            100% { width: 100%; }
        }
        
        .field-error {
            animation: shake 0.5s ease-in-out;
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
        
        .form-success {
            animation: slideInDown 0.3s ease-out;
        }
        
        @keyframes slideInDown {
            from {
                transform: translateY(-20px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);

    // Loading complete animation
    window.addEventListener('load', () => {
        document.body.classList.add('loaded');
        
        // Trigger initial animations
        const heroElements = document.querySelectorAll('.fade-in-up');
        heroElements.forEach((element, index) => {
            setTimeout(() => {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, index * 200);
        });
    });

    console.log('🚀 Django AI Builder Landing Page Loaded Successfully!');
});

// Expose utility functions for external use
window.LandingPageUtils = {
    smoothScrollTo: function(target) {
        const targetElement = document.querySelector(target);
        if (targetElement) {
            targetElement.scrollIntoView({ behavior: 'smooth' });
        }
    }
};