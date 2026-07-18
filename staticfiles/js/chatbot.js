// Enhanced Chatbot JavaScript with Natural Conversation Handling
class ChatBot {
    constructor() {
        this.isOpen = false;
        this.isTyping = false;
        this.conversationHistory = [];
        this.welcomeShown = false;
        this.init();
    }

    init() {
        this.createChatbotHTML();
        this.bindEvents();
        this.loadConversationHistory();
        this.checkFirstVisit();
        this.getUsername();
    }

    getUsername() {
        // Check if user is logged in by looking for username in the DOM
        const profileLink = document.querySelector('[href*="profile"]');
        const usernameElement = document.querySelector('.username, .user-name, [data-username]');
        this.username = usernameElement?.textContent || 'Friend';
    }

    createChatbotHTML() {
        const chatbotHTML = `
            <div class="chatbot-container">
                <button class="chatbot-toggle" id="chatbotToggle">
                    <span class="icon">💬</span>
                    <span class="notification-badge" id="notificationBadge" style="display: none;"></span>
                </button>
                
                <div class="chatbot-window" id="chatbotWindow">
                    <div class="chatbot-header">
                        <div class="header-info">
                            <div class="avatar">🤖</div>
                            <div class="header-text">
                                <h3>Shopping Assistant</h3>
                                <div class="status">
                                    <span class="status-dot"></span>
                                    <span>Online</span>
                                </div>
                            </div>
                        </div>
                        <button class="close-btn" id="closeChatbot">
                            <span>✕</span>
                        </button>
                    </div>
                    
                    <div class="chatbot-messages" id="chatbotMessages">
                        <div class="welcome-message" id="welcomeMessage">
                            <div class="avatar">🤖</div>
                            <h4 id="welcomeGreeting">Welcome! 👋</h4>
                            <p id="welcomeText">I'm here to help with orders, payments, offers, and more!</p>
                            <div class="welcome-quick-replies">
                                <button class="welcome-quick-reply" data-message="Orders">
                                    📦 Track Orders
                                </button>
                                <button class="welcome-quick-reply" data-message="Payment">
                                    💳 Payment Help
                                </button>
                                <button class="welcome-quick-reply" data-message="Offers">
                                    🎁 Active Offers
                                </button>
                                <button class="welcome-quick-reply" data-message="Products">
                                    🛍️ Find Products
                                </button>
                            </div>
                        </div>
                        
                        <div class="typing-indicator" id="typingIndicator">
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                        </div>
                    </div>
                    
                    <div class="chatbot-input">
                        <form class="chatbot-input-form" id="chatbotForm">
                            <input 
                                type="text" 
                                id="chatbotInput" 
                                placeholder="Type your message..."
                                autocomplete="off"
                                required
                            />
                            <button type="submit" class="send-btn" id="sendBtn">
                                <span>➤</span>
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', chatbotHTML);
    }

    bindEvents() {
        // Toggle chatbot
        document.getElementById('chatbotToggle').addEventListener('click', () => this.toggleChatbot());
        document.getElementById('closeChatbot').addEventListener('click', () => this.closeChatbot());
        
        // Send message
        document.getElementById('chatbotForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });
        
        // Quick reply buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('quick-reply-btn') || 
                e.target.classList.contains('welcome-quick-reply')) {
                const message = e.target.getAttribute('data-message') || e.target.textContent.trim();
                this.sendQuickReply(message);
            }
        });
        
        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.chatbot-container') && this.isOpen) {
                this.closeChatbot();
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.closeChatbot();
            }
            if (e.key === 'Enter' && !e.shiftKey && document.activeElement.id === 'chatbotInput') {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize input
        const input = document.getElementById('chatbotInput');
        input.addEventListener('input', () => {
            this.autoResizeInput(input);
        });
    }

    toggleChatbot() {
        if (this.isOpen) {
            this.closeChatbot();
        } else {
            this.openChatbot();
        }
    }

    openChatbot() {
        this.isOpen = true;
        const window = document.getElementById('chatbotWindow');
        window.classList.add('active');
        
        // Hide notification badge
        document.getElementById('notificationBadge').style.display = 'none';
        
        // Focus input
        setTimeout(() => {
            document.getElementById('chatbotInput').focus();
        }, 300);
        
        // Show welcome message if first visit
        if (!this.welcomeShown) {
            this.showWelcomeMessage();
        }
    }

    closeChatbot() {
        this.isOpen = false;
        const window = document.getElementById('chatbotWindow');
        window.classList.remove('active');
    }

    showWelcomeMessage() {
        const welcomeMessage = document.getElementById('welcomeMessage');
        const welcomeGreeting = document.getElementById('welcomeGreeting');
        const welcomeText = document.getElementById('welcomeText');
        
        if (welcomeMessage) {
            // Set personalized greeting
            if (this.username && this.username !== 'Friend') {
                welcomeGreeting.textContent = `Hi ${this.username}! 👋`;
                welcomeText.textContent = 'Welcome back! How can I help you today?';
            } else {
                welcomeGreeting.textContent = 'Hi there! 👋';
                welcomeText.textContent = 'Welcome to Meesho! How can I help you?';
            }
            
            welcomeMessage.style.display = 'block';
            this.welcomeShown = true;
            
            // Hide welcome after first user interaction
            setTimeout(() => {
                if (this.conversationHistory.length === 0) {
                    welcomeMessage.style.display = 'none';
                }
            }, 30000); // Hide after 30 seconds if no interaction
        }
    }

    hideWelcomeMessage() {
        const welcomeMessage = document.getElementById('welcomeMessage');
        if (welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }
    }

    sendMessage() {
        const input = document.getElementById('chatbotInput');
        const message = input.value.trim();
        
        if (!message || this.isTyping) return;
        
        // Hide welcome message
        this.hideWelcomeMessage();
        
        // Add user message
        this.addMessage(message, 'user');
        input.value = '';
        this.autoResizeInput(input);
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Send to backend
        this.sendToBackend(message);
    }

    sendQuickReply(message) {
        if (this.isTyping) return;
        
        // Hide welcome message
        this.hideWelcomeMessage();
        
        // Add user message
        this.addMessage(message, 'user');
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Send to backend
        this.sendToBackend(message);
    }

    async sendToBackend(message) {
        this.isTyping = true;
        
        try {
            const response = await fetch('/api/chatbot/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Hide typing indicator
                this.hideTypingIndicator();
                
                // Add bot response
                this.addMessage(data.response, 'bot', data.quick_replies);
                
                // Save to history
                this.conversationHistory.push({
                    user: message,
                    bot: data.response,
                    timestamp: new Date().toISOString()
                });
                
                this.saveConversationHistory();
                
                // Update quick replies based on context
                this.updateQuickReplies(data.quick_replies);
                
            } else {
                this.hideTypingIndicator();
                this.addMessage("Sorry, I'm having trouble responding. Please try again.", 'bot');
            }
        } catch (error) {
            console.error('Chatbot error:', error);
            this.hideTypingIndicator();
            this.addMessage("Connection error. Please check your internet and try again.", 'bot');
        } finally {
            this.isTyping = false;
        }
    }

    addMessage(text, sender, quickReplies = []) {
        const messagesContainer = document.getElementById('chatbotMessages');
        const typingIndicator = document.getElementById('typingIndicator');
        
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';
        
        // Format message text
        const formattedText = this.formatMessage(text);
        
        bubbleDiv.innerHTML = `
            <p class="message-text">${formattedText}</p>
            <span class="message-time">${this.getCurrentTime()}</span>
        `;
        
        messageDiv.appendChild(bubbleDiv);
        
        // Add quick replies if provided
        if (quickReplies && quickReplies.length > 0) {
            const quickRepliesDiv = document.createElement('div');
            quickRepliesDiv.className = 'quick-replies';
            
            quickReplies.forEach(reply => {
                const btn = document.createElement('button');
                btn.className = 'quick-reply-btn';
                btn.textContent = reply;
                btn.setAttribute('data-message', reply);
                quickRepliesDiv.appendChild(btn);
            });
            
            messageDiv.appendChild(quickRepliesDiv);
        }
        
        // Insert before typing indicator
        messagesContainer.insertBefore(messageDiv, typingIndicator);
        
        // Scroll to bottom
        this.scrollToBottom();
        
        // Add animation
        setTimeout(() => {
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 10);
    }

    formatMessage(text) {
        // Convert markdown-like formatting to HTML
        let formatted = text;
        
        // Bold text
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Line breaks
        formatted = formatted.replace(/\n\n/g, '<br><br>');
        formatted = formatted.replace(/\n/g, '<br>');
        
        // Emojis (keep as is)
        
        return formatted;
    }

    showTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        indicator.classList.add('active');
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        indicator.classList.remove('active');
    }

    updateQuickReplies(quickReplies) {
        // This can be used to dynamically update context-aware quick replies
        // Implementation depends on specific requirements
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chatbotMessages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: true 
        });
    }

    autoResizeInput(input) {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 100) + 'px';
    }

    getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(cookie => cookie.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }

    saveConversationHistory() {
        try {
            localStorage.setItem('chatbotHistory', JSON.stringify(this.conversationHistory));
        } catch (error) {
            console.warn('Could not save conversation history:', error);
        }
    }

    loadConversationHistory() {
        try {
            const saved = localStorage.getItem('chatbotHistory');
            if (saved) {
                this.conversationHistory = JSON.parse(saved);
            }
        } catch (error) {
            console.warn('Could not load conversation history:', error);
        }
    }

    checkFirstVisit() {
        const hasVisited = localStorage.getItem('chatbotVisited');
        if (!hasVisited) {
            // Show notification badge for first-time visitors
            document.getElementById('notificationBadge').style.display = 'block';
            localStorage.setItem('chatbotVisited', 'true');
        }
    }

    // Public method to trigger chatbot from outside
    openWithMessage(message) {
        this.openChatbot();
        setTimeout(() => {
            this.sendQuickReply(message);
        }, 500);
    }
}

// Initialize chatbot when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatBot = new ChatBot();
    
    // Make chatbot available globally for external calls
    window.openChatBot = (message) => {
        window.chatBot.openWithMessage(message);
    };
    
    // Add some helpful console messages
    console.log('🤖 Chatbot initialized! Use window.openChatBot("message") to open with a message.');
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden && window.chatBot) {
        // Save state when page is hidden
        window.chatBot.saveConversationHistory();
    }
});

// Handle beforeunload to save conversation
window.addEventListener('beforeunload', () => {
    if (window.chatBot) {
        window.chatBot.saveConversationHistory();
    }
});
