// AI Features - Modern Interactive JavaScript

class AIShoppingAssistant {
    constructor() {
        this.init();
        this.userBehavior = [];
        this.voiceRecognition = null;
        this.currentRecording = false;
    }

    init() {
        this.setupEventListeners();
        this.loadAIRecommendations();
        this.checkWishlistReminders();
        this.initVoiceSearch();
        this.setupVirtualTryOn();
        this.trackUserBehavior();
    }

    setupEventListeners() {
        // Track product views
        document.addEventListener('DOMContentLoaded', () => {
            this.trackPageView();
        });

        // Voice search button
        const voiceBtn = document.querySelector('.voice-search-btn');
        if (voiceBtn) {
            voiceBtn.addEventListener('click', () => this.toggleVoiceSearch());
        }

        // Virtual try-on upload
        const tryonUpload = document.querySelector('.tryon-upload-area');
        if (tryonUpload) {
            tryonUpload.addEventListener('click', () => this.triggerTryOnUpload());
            tryonUpload.addEventListener('dragover', (e) => this.handleDragOver(e));
            tryonUpload.addEventListener('drop', (e) => this.handleFileDrop(e));
        }

        // AI Assistant FAB
        const aiFab = document.querySelector('.ai-assistant-fab');
        const aiPanel = document.querySelector('.ai-assistant-panel');
        if (aiFab && aiPanel) {
            aiFab.addEventListener('click', () => {
                aiPanel.classList.toggle('active');
            });
        }

        // Recommendation clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.recommendation-card')) {
                this.trackRecommendationClick(e.target.closest('.recommendation-card'));
            }
        });

        // Wishlist reminder actions
        document.addEventListener('click', (e) => {
            if (e.target.closest('.reminder-actions')) {
                this.handleWishlistReminder(e.target.closest('.reminder-actions'));
            }
        });
    }

    // AI Recommendations
    async loadAIRecommendations() {
        try {
            const response = await fetch('/api/ai/recommendations/');
            const data = await response.json();
            
            if (data.success && data.recommendations.length > 0) {
                this.renderRecommendations(data.recommendations);
            }
        } catch (error) {
            console.error('Error loading recommendations:', error);
        }
    }

    renderRecommendations(recommendations) {
        const container = document.querySelector('.ai-recommendations .recommendation-grid');
        if (!container) return;

        container.innerHTML = recommendations.map(product => `
            <div class="recommendation-card" data-product-id="${product.id}">
                <div class="ai-badge">AI Pick</div>
                <img src="${product.image || '/static/images/default-product.jpg'}" alt="${product.name}">
                <div class="card-body">
                    <h5>${product.name}</h5>
                    <div class="price">₹${product.price}</div>
                    <button class="btn btn-sm btn-primary mt-2" onclick="addToCart('${product.id}')">
                        Add to Cart
                    </button>
                </div>
            </div>
        `).join('');
    }

    trackRecommendationClick(card) {
        const productId = card.dataset.productId;
        this.trackBehavior(productId, 'recommendation_click');
    }

    // Smart Wishlist
    async addToWishlist(productId) {
        try {
            const response = await fetch(`/api/ai/wishlist/add/${productId}/`);
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Added to wishlist!', 'success');
                this.trackBehavior(productId, 'wishlist');
                this.checkForOffers(productId);
            }
        } catch (error) {
            console.error('Error adding to wishlist:', error);
        }
    }

    async removeFromWishlist(productId) {
        try {
            const response = await fetch(`/api/ai/wishlist/remove/${productId}/`);
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Removed from wishlist', 'info');
                
                if (data.feedback_request) {
                    this.showFeedbackModal(productId, data.suggestions);
                }
            }
        } catch (error) {
            console.error('Error removing from wishlist:', error);
        }
    }

    showFeedbackModal(productId, suggestions) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Why did you remove this item?</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Your feedback helps us improve recommendations!</p>
                        <div class="feedback-options">
                            <button class="btn btn-outline-secondary me-2">Too expensive</button>
                            <button class="btn btn-outline-secondary me-2">Not interested</button>
                            <button class="btn btn-outline-secondary me-2">Found better</button>
                            <button class="btn btn-outline-secondary">Other</button>
                        </div>
                        ${suggestions && suggestions.length > 0 ? `
                            <div class="mt-4">
                                <h6>You might also like:</h6>
                                <div class="row">
                                    ${suggestions.map(p => `
                                        <div class="col-md-4 mb-3">
                                            <div class="card">
                                                <img src="${p.image || '/static/images/default-product.jpg'}" class="card-img-top" alt="${p.name}">
                                                <div class="card-body p-2">
                                                    <h6 class="card-title small">${p.name}</h6>
                                                    <div class="price">₹${p.price}</div>
                                                </div>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
        
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }

    // Smart Offers
    async checkForOffers(productId) {
        try {
            const response = await fetch('/api/ai/offers/');
            const data = await response.json();
            
            if (data.success && data.offers.length > 0) {
                this.showOffers(data.offers);
            }
        } catch (error) {
            console.error('Error checking offers:', error);
        }
    }

    showOffers(offers) {
        const offersContainer = document.querySelector('.smart-offers');
        if (!offersContainer) return;

        offersContainer.innerHTML = offers.map(offer => `
            <div class="offer-banner">
                <h3>Special Offer Just for You! 🎉</h3>
                <div class="offer-discount">${offer.discount}% OFF</div>
                <p>${offer.trigger_reason}</p>
                <div class="offer-timer">
                    Expires in: ${this.getTimeRemaining(offer.expires_at)}
                </div>
                <button class="btn btn-light mt-3" onclick="applyOffer('${offer.id}')">
                    Apply Offer
                </button>
            </div>
        `).join('');

        offersContainer.style.display = 'block';
    }

    getTimeRemaining(expiresAt) {
        const now = new Date();
        const expiry = new Date(expiresAt);
        const diff = expiry - now;
        
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        
        return `${hours}h ${minutes}m`;
    }

    // Voice Search
    initVoiceSearch() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.voiceRecognition = new SpeechRecognition();
            this.voiceRecognition.continuous = false;
            this.voiceRecognition.interimResults = false;
            this.voiceRecognition.lang = 'en-US';

            this.voiceRecognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                this.handleVoiceResult(transcript);
            };

            this.voiceRecognition.onerror = (event) => {
                console.error('Voice recognition error:', event.error);
                this.stopVoiceRecording();
            };

            this.voiceRecognition.onend = () => {
                this.stopVoiceRecording();
            };
        }
    }

    toggleVoiceSearch() {
        if (!this.voiceRecognition) {
            this.showNotification('Voice search not supported in your browser', 'warning');
            return;
        }

        if (this.currentRecording) {
            this.stopVoiceRecording();
        } else {
            this.startVoiceRecording();
        }
    }

    startVoiceRecording() {
        this.voiceRecognition.start();
        this.currentRecording = true;
        
        const voiceBtn = document.querySelector('.voice-search-btn');
        if (voiceBtn) {
            voiceBtn.classList.add('recording');
        }
        
        this.showNotification('Listening... Speak now!', 'info');
    }

    stopVoiceRecording() {
        if (this.voiceRecognition && this.currentRecording) {
            this.voiceRecognition.stop();
        }
        
        this.currentRecording = false;
        
        const voiceBtn = document.querySelector('.voice-search-btn');
        if (voiceBtn) {
            voiceBtn.classList.remove('recording');
        }
    }

    async handleVoiceResult(query) {
        try {
            const response = await fetch('/api/ai/voice-search/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ query: query })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayVoiceResults(data);
                this.trackBehavior(null, 'voice_search', { query: data.query });
            }
        } catch (error) {
            console.error('Error processing voice search:', error);
        }
    }

    displayVoiceResults(data) {
        const resultsContainer = document.querySelector('.voice-results');
        if (!resultsContainer) return;

        resultsContainer.innerHTML = `
            <div class="voice-query">
                <strong>You said:</strong> "${data.query}"
            </div>
            <div class="results-count">
                Found ${data.results_count} products
            </div>
            <div class="row mt-3">
                ${data.products.map(product => `
                    <div class="col-md-3 mb-3">
                        <div class="card">
                            <img src="${product.image || '/static/images/default-product.jpg'}" class="card-img-top" alt="${product.name}">
                            <div class="card-body">
                                <h6 class="card-title">${product.name}</h6>
                                <div class="price">₹${product.price}</div>
                                <a href="/product/${product.slug}/" class="btn btn-primary btn-sm">View</a>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        resultsContainer.style.display = 'block';
    }

    // Virtual Try-On
    setupVirtualTryOn() {
        // Setup is done in event listeners
    }

    triggerTryOnUpload() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.onchange = (e) => this.handleTryOnFile(e.target.files[0]);
        input.click();
    }

    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('dragover');
    }

    handleFileDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.handleTryOnFile(files[0]);
        }
    }

    async handleTryOnFile(file) {
        if (!file.type.startsWith('image/')) {
            this.showNotification('Please upload an image file', 'warning');
            return;
        }

        const formData = new FormData();
        formData.append('user_image', file);
        formData.append('try_on_type', 'clothing');

        try {
            const productId = document.querySelector('[data-product-id]')?.dataset.productId;
            if (!productId) {
                this.showNotification('Please select a product first', 'warning');
                return;
            }

            const response = await fetch(`/api/ai/virtual-tryon/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: formData
            });

            const data = await response.json();
            
            if (data.success) {
                this.displayTryOnResult(data);
            }
        } catch (error) {
            console.error('Error with virtual try-on:', error);
        }
    }

    displayTryOnResult(data) {
        const resultContainer = document.querySelector('.tryon-result');
        if (!resultContainer) return;

        resultContainer.innerHTML = `
            <h5>Virtual Try-On Result ✨</h5>
            <p>Your virtual try-on has been processed!</p>
            ${data.result_image ? `<img src="${data.result_image}" class="img-fluid rounded" alt="Virtual Try-On Result">` : ''}
            <div class="mt-3">
                <button class="btn btn-primary">Save Look</button>
                <button class="btn btn-outline-secondary ms-2">Share</button>
            </div>
        `;
        
        resultContainer.style.display = 'block';
    }

    // Wishlist Reminders
    async checkWishlistReminders() {
        try {
            const response = await fetch('/api/ai/wishlist/reminders/');
            const data = await response.json();
            
            if (data.success && data.reminders.length > 0) {
                this.showWishlistReminders(data.reminders);
            }
        } catch (error) {
            console.error('Error checking wishlist reminders:', error);
        }
    }

    showWishlistReminders(reminders) {
        const container = document.querySelector('.wishlist-reminders');
        if (!container) return;

        container.innerHTML = reminders.map(reminder => `
            <div class="wishlist-reminder" data-product-id="${reminder.product_id}">
                <h6>⏰ Still interested?</h6>
                <p>${reminder.message}</p>
                <div class="reminder-actions">
                    <button class="btn btn-primary" onclick="moveToCart('${reminder.product_id}')">
                        Move to Cart
                    </button>
                    <button class="btn btn-secondary" onclick="removeFromWishlist('${reminder.product_id}')">
                        Remove
                    </button>
                </div>
            </div>
        `).join('');
        
        container.style.display = 'block';
    }

    handleWishlistReminder(actionsContainer) {
        // Handle reminder actions
    }

    // User Behavior Tracking
    trackBehavior(productId, actionType, additionalData = {}) {
        const behavior = {
            product_id: productId,
            action_type: actionType,
            timestamp: new Date().toISOString(),
            ...additionalData
        };

        this.userBehavior.push(behavior);

        // Send to server
        this.sendBehaviorData(behavior);
    }

    async sendBehaviorData(behavior) {
        try {
            await fetch('/api/ai/track-behavior/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(behavior)
            });
        } catch (error) {
            console.error('Error tracking behavior:', error);
        }
    }

    trackPageView() {
        const productId = document.querySelector('[data-product-id]')?.dataset.productId;
        if (productId) {
            this.trackBehavior(productId, 'view');
        }
    }

    // Seller Trust Scores
    async loadSellerTrustScores() {
        const sellerElements = document.querySelectorAll('[data-seller-id]');
        
        for (const element of sellerElements) {
            const sellerId = element.dataset.sellerId;
            try {
                const response = await fetch(`/api/ai/seller-trust/${sellerId}/`);
                const data = await response.json();
                
                if (data.success) {
                    this.renderSellerTrustBadge(element, data);
                }
            } catch (error) {
                console.error('Error loading seller trust score:', error);
            }
        }
    }

    renderSellerTrustBadge(element, trustData) {
        const badge = document.createElement('div');
        badge.className = `seller-trust-badge ${
            trustData.is_verified ? 'trust-verified' : 
            trustData.trust_score < 50 ? 'trust-warning' : 'trust-score'
        }`;
        
        badge.innerHTML = `
            <span>${trustData.is_verified ? '✅ Verified' : '⚠️ Check'}</span>
            <span class="trust-score-value">${trustData.trust_score.toFixed(1)}%</span>
        `;
        
        element.appendChild(badge);
    }

    // Utility Functions
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    getCSRFToken() {
        const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    }

    // Load trending products
    async loadTrendingProducts() {
        try {
            const response = await fetch('/api/ai/trending/');
            const data = await response.json();
            
            if (data.success) {
                this.renderTrendingProducts(data.products);
            }
        } catch (error) {
            console.error('Error loading trending products:', error);
        }
    }

    renderTrendingProducts(products) {
        const container = document.querySelector('.trending-products-grid');
        if (!container) return;

        container.innerHTML = products.map(product => `
            <div class="col-md-3 mb-4">
                <div class="card trending-card">
                    <div class="trending-badge">🔥 Trending</div>
                    <img src="${product.image || '/static/images/default-product.jpg'}" class="card-img-top" alt="${product.name}">
                    <div class="card-body">
                        <h6 class="card-title">${product.name}</h6>
                        <div class="price">₹${product.price}</div>
                        <div class="trending-stats">
                            <small>👁 ${product.view_count || 0} views</small><br>
                            <small>❤️ ${product.wishlist_count || 0} wishlists</small>
                        </div>
                        <a href="/product/${product.slug}/" class="btn btn-primary btn-sm mt-2">View</a>
                    </div>
                </div>
            </div>
        `).join('');
    }
}

// Initialize AI Shopping Assistant
const aiAssistant = new AIShoppingAssistant();

// Global functions for onclick handlers
window.addToWishlist = (productId) => aiAssistant.addToWishlist(productId);
window.removeFromWishlist = (productId) => aiAssistant.removeFromWishlist(productId);
window.moveToCart = (productId) => {
    // Implementation for moving to cart
    aiAssistant.showNotification('Moved to cart!', 'success');
};

// Load trending products on shop pages
if (document.querySelector('.trending-products-grid')) {
    aiAssistant.loadTrendingProducts();
}

// Load seller trust scores on product pages
if (document.querySelector('[data-seller-id]')) {
    aiAssistant.loadSellerTrustScores();
}
