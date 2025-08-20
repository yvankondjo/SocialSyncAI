/**
 * SocialSync Chat Widget - JavaScript Client
 * Version 1.0.0
 * 
 * Widget de chat IA intégrable sur n'importe quel site web
 */

(function() {
    'use strict';
    
    // Vérifier que le widget n'est pas déjà chargé
    if (window.SocialSyncChatWidget) {
        console.warn('SocialSync Widget déjà chargé');
        return;
    }
    
    class SocialSyncChatWidget {
        constructor() {
            this.config = null;
            this.isOpen = false;
            this.conversationId = null;
            this.messages = [];
            this.isTyping = false;
            this.elements = {};
            
            // Bind methods
            this.init = this.init.bind(this);
            this.toggle = this.toggle.bind(this);
            this.sendMessage = this.sendMessage.bind(this);
            this.handleKeyPress = this.handleKeyPress.bind(this);
        }
        
        init(config) {
            this.config = {
                widgetId: config.widgetId,
                apiKey: config.apiKey, 
                apiUrl: config.apiUrl || 'http://localhost:8000',
                debug: config.debug || false,
                // Paramètres par défaut (seront écrasés par la config serveur)
                theme: 'light',
                primaryColor: '#007bff',
                position: 'bottom-right',
                welcomeMessage: 'Bonjour ! Comment puis-je vous aider ?',
                placeholderText: 'Tapez votre message...',
                companyName: 'Support',
                autoOpen: false,
                autoOpenDelay: 3000
            };
            
            this.log('Initialisation du widget', this.config);
            
            // Charger la configuration depuis le serveur
            this.loadConfig()
                .then(() => {
                    this.createWidget();
                    this.setupEventListeners();
                    
                    if (this.config.autoOpen) {
                        setTimeout(() => this.open(), this.config.autoOpenDelay);
                    }
                })
                .catch(error => {
                    console.error('Erreur initialisation widget:', error);
                    // Créer le widget avec la config par défaut
                    this.createWidget();
                    this.setupEventListeners();
                });
        }
        
        async loadConfig() {
            try {
                const response = await fetch(`${this.config.apiUrl}/api/widget/config/${this.config.widgetId}`, {
                    headers: {
                        'Authorization': `Bearer ${this.config.apiKey}`,
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const serverConfig = await response.json();
                    Object.assign(this.config, serverConfig.settings);
                    this.log('Configuration chargée depuis le serveur', serverConfig);
                }
            } catch (error) {
                this.log('Erreur chargement config serveur:', error);
                // Continuer avec la config par défaut
            }
        }
        
        createWidget() {
            this.log('Création de l\'interface widget');
            
            // Créer le bouton du widget
            this.createWidgetButton();
            
            // Créer la fenêtre de chat
            this.createChatWindow();
            
            // Appliquer le thème
            this.applyTheme();
            
            // Injecter dans le DOM
            document.body.appendChild(this.elements.container);
            
            this.log('Widget créé et injecté dans le DOM');
        }
        
        createWidgetButton() {
            const button = document.createElement('div');
            button.className = 'socialsync-widget-button';
            button.innerHTML = `
                <div class="button-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M20 2H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h4l4 4 4-4h4a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z" 
                              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <div class="button-close" style="display: none;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                        <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                </div>
            `;
            
            button.addEventListener('click', this.toggle);
            this.elements.button = button;
        }
        
        createChatWindow() {
            const chatWindow = document.createElement('div');
            chatWindow.className = 'socialsync-chat-window';
            chatWindow.style.display = 'none';
            
            chatWindow.innerHTML = `
                <div class="chat-header">
                    <div class="header-info">
                        <div class="company-name">${this.config.companyName}</div>
                        <div class="status-indicator">
                            <span class="status-dot"></span>
                            En ligne
                        </div>
                    </div>
                    <button class="close-button">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                            <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
                            <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
                        </svg>
                    </button>
                </div>
                
                <div class="chat-messages">
                    <div class="welcome-message">
                        <div class="message-avatar">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                                <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                            </svg>
                        </div>
                        <div class="message-content">
                            <div class="message-text">${this.config.welcomeMessage}</div>
                            <div class="message-time">À l'instant</div>
                        </div>
                    </div>
                </div>
                
                <div class="typing-indicator" style="display: none;">
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                    <span class="typing-text">L'assistant écrit...</span>
                </div>
                
                <div class="chat-input-container">
                    <div class="chat-input">
                        <input type="text" placeholder="${this.config.placeholderText}" maxlength="1000">
                        <button class="send-button">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                                <line x1="22" y1="2" x2="11" y2="13" stroke="currentColor" stroke-width="2"/>
                                <polygon points="22,2 15,22 11,13 2,9 22,2" fill="currentColor"/>
                            </svg>
                        </button>
                    </div>
                    <div class="powered-by">
                        Powered by <strong>SocialSync AI</strong>
                    </div>
                </div>
            `;
            
            // Créer le container principal
            const container = document.createElement('div');
            container.className = 'socialsync-widget-container';
            container.appendChild(this.elements.button);
            container.appendChild(chatWindow);
            
            this.elements.container = container;
            this.elements.chatWindow = chatWindow;
            this.elements.messagesContainer = chatWindow.querySelector('.chat-messages');
            this.elements.input = chatWindow.querySelector('input');
            this.elements.sendButton = chatWindow.querySelector('.send-button');
            this.elements.closeButton = chatWindow.querySelector('.close-button');
            this.elements.typingIndicator = chatWindow.querySelector('.typing-indicator');
        }
        
        applyTheme() {
            const root = this.elements.container;
            const position = this.config.position || 'bottom-right';
            
            // Appliquer la position
            root.classList.add(`position-${position}`);
            
            // Appliquer les variables CSS
            root.style.setProperty('--primary-color', this.config.primaryColor);
            root.style.setProperty('--theme', this.config.theme);
            
            if (this.config.theme === 'dark') {
                root.classList.add('theme-dark');
            }
        }
        
        setupEventListeners() {
            // Bouton d'envoi
            this.elements.sendButton.addEventListener('click', this.sendMessage);
            
            // Entrée clavier
            this.elements.input.addEventListener('keypress', this.handleKeyPress);
            
            // Bouton fermeture
            this.elements.closeButton.addEventListener('click', this.close.bind(this));
            
            // Redimensionnement de la fenêtre
            window.addEventListener('resize', this.handleResize.bind(this));
            
            this.log('Event listeners configurés');
        }
        
        handleKeyPress(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                this.sendMessage();
            }
        }
        
        async sendMessage() {
            const input = this.elements.input;
            const message = input.value.trim();
            
            if (!message) return;
            
            this.log('Envoi du message:', message);
            
            // Ajouter le message utilisateur
            this.addMessage(message, 'user');
            
            // Vider l'input
            input.value = '';
            
            // Afficher l'indicateur de frappe
            this.showTypingIndicator();
            
            try {
                // Envoyer à l'API
                const response = await fetch(`${this.config.apiUrl}/api/widget/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        widget_id: this.config.widgetId,
                        message: message,
                        conversation_id: this.conversationId,
                        user_info: this.getUserInfo()
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.conversationId = data.conversation_id;
                    
                    // Simuler un délai de frappe réaliste
                    setTimeout(() => {
                        this.hideTypingIndicator();
                        this.addMessage(data.ai_response, 'bot');
                    }, Math.random() * 1000 + 500);
                    
                } else {
                    throw new Error(data.error || 'Erreur inconnue');
                }
                
            } catch (error) {
                this.log('Erreur envoi message:', error);
                this.hideTypingIndicator();
                
                const fallbackMessage = "Désolé, je rencontre des difficultés techniques. Un agent humain vous contactera bientôt.";
                this.addMessage(fallbackMessage, 'bot');
            }
        }
        
        addMessage(text, sender) {
            const messageElement = document.createElement('div');
            messageElement.className = `message ${sender}`;
            
            const time = new Date().toLocaleTimeString('fr-FR', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            
            if (sender === 'bot') {
                messageElement.innerHTML = `
                    <div class="message-avatar">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                            <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                        </svg>
                    </div>
                    <div class="message-content">
                        <div class="message-text">${this.escapeHtml(text)}</div>
                        <div class="message-time">${time}</div>
                    </div>
                `;
            } else {
                messageElement.innerHTML = `
                    <div class="message-content">
                        <div class="message-text">${this.escapeHtml(text)}</div>
                        <div class="message-time">${time}</div>
                    </div>
                `;
            }
            
            this.elements.messagesContainer.appendChild(messageElement);
            this.scrollToBottom();
            
            // Sauvegarder le message
            this.messages.push({ text, sender, time });
        }
        
        showTypingIndicator() {
            this.isTyping = true;
            this.elements.typingIndicator.style.display = 'flex';
            this.scrollToBottom();
        }
        
        hideTypingIndicator() {
            this.isTyping = false;
            this.elements.typingIndicator.style.display = 'none';
        }
        
        scrollToBottom() {
            setTimeout(() => {
                this.elements.messagesContainer.scrollTop = this.elements.messagesContainer.scrollHeight;
            }, 100);
        }
        
        toggle() {
            if (this.isOpen) {
                this.close();
            } else {
                this.open();
            }
        }
        
        open() {
            this.isOpen = true;
            this.elements.chatWindow.style.display = 'block';
            this.elements.button.querySelector('.button-icon').style.display = 'none';
            this.elements.button.querySelector('.button-close').style.display = 'block';
            this.elements.input.focus();
            
            this.log('Widget ouvert');
        }
        
        close() {
            this.isOpen = false;
            this.elements.chatWindow.style.display = 'none';
            this.elements.button.querySelector('.button-icon').style.display = 'block';
            this.elements.button.querySelector('.button-close').style.display = 'none';
            
            this.log('Widget fermé');
        }
        
        handleResize() {
            // Ajuster la taille sur mobile
            if (window.innerWidth <= 768) {
                this.elements.container.classList.add('mobile');
            } else {
                this.elements.container.classList.remove('mobile');
            }
        }
        
        getUserInfo() {
            // Collecter les infos utilisateur si nécessaire
            return {
                userAgent: navigator.userAgent,
                url: window.location.href,
                referrer: document.referrer,
                timestamp: new Date().toISOString()
            };
        }
        
        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        log(...args) {
            if (this.config && this.config.debug) {
                console.log('[SocialSync Widget]', ...args);
            }
        }
        
        // API publique pour les développeurs
        destroy() {
            if (this.elements.container) {
                this.elements.container.remove();
            }
            this.log('Widget détruit');
        }
        
        setUserInfo(userInfo) {
            this.userInfo = userInfo;
            this.log('Infos utilisateur mises à jour:', userInfo);
        }
        
        sendCustomMessage(message) {
            this.elements.input.value = message;
            this.sendMessage();
        }
    }
    
    // Exposer la classe globalement
    window.SocialSyncChatWidget = new SocialSyncChatWidget();
    
    // Auto-initialisation si la config est déjà disponible
    if (window.SocialSyncWidget) {
        window.SocialSyncChatWidget.init(window.SocialSyncWidget);
    }
    
})();
