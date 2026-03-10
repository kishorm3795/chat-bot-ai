/**
 * AI Student Chatbot - Embeddable Widget
 * 
 * Usage:
 * <script src="https://your-server.com/student-bot.js"></script>
 * <script>
 *   StudentBot.init({
 *     apiUrl: "https://your-server.com/chat",
 *     title: "AI Assistant"
 *   });
 * </script>
 */

(function() {
    'use strict';

    // Default configuration
    const DEFAULT_CONFIG = {
        apiUrl: 'http://localhost:8000/chat',
        title: 'AI Student Assistant',
        welcomeMessage: 'Hello! I\'m your AI assistant. How can I help you today?',
        primaryColor: '#4F46E5',
        position: 'bottom-right',
        backgroundColor: '#ffffff',
        textColor: '#1F2937',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    };

    // CSS Styles (injected dynamically)
    const STYLES = `
        :root {
            --sb-primary: var(--sb-primary-color, ${DEFAULT_CONFIG.primaryColor});
            --sb-bg: var(--sb-bg-color, ${DEFAULT_CONFIG.backgroundColor});
            --sb-text: var(--sb-text-color, ${DEFAULT_CONFIG.textColor});
            --sb-font: var(--sb-font-family, ${DEFAULT_CONFIG.fontFamily});
        }

        #sb-widget {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 99999;
            font-family: var(--sb-font);
        }

        #sb-button {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: var(--sb-primary);
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        #sb-button:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 16px rgba(0,0,0,0.2);
        }

        #sb-button svg {
            width: 28px;
            height: 28px;
            fill: white;
        }

        #sb-container {
            position: absolute;
            bottom: 80px;
            right: 0;
            width: 380px;
            max-width: calc(100vw - 40px);
            height: 520px;
            max-height: calc(100vh - 120px);
            background: var(--sb-bg);
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
            display: none;
            flex-direction: column;
            overflow: hidden;
        }

        #sb-container.open {
            display: flex;
            animation: sbSlideUp 0.3s ease;
        }

        @keyframes sbSlideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        #sb-header {
            background: var(--sb-primary);
            color: white;
            padding: 16px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        #sb-header-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: var(--sb-primary);
            font-size: 14px;
        }

        #sb-header-info h3 {
            font-size: 16px;
            margin: 0;
        }

        #sb-header-info p {
            font-size: 12px;
            opacity: 0.9;
            margin: 0;
        }

        #sb-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .sb-message {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: 16px;
            font-size: 14px;
            line-height: 1.5;
            word-wrap: break-word;
        }

        .sb-message.sb-user {
            align-self: flex-end;
            background: var(--sb-primary);
            color: white;
            border-bottom-right-radius: 4px;
        }

        .sb-message.sb-bot {
            align-self: flex-start;
            background: #f3f4f6;
            color: var(--sb-text);
            border-bottom-left-radius: 4px;
        }

        .sb-typing {
            display: flex;
            gap: 4px;
            padding: 12px 16px;
        }

        .sb-typing span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #9ca3af;
            animation: sbTyping 1.4s infinite;
        }

        .sb-typing span:nth-child(2) { animation-delay: 0.2s; }
        .sb-typing span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes sbTyping {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
            30% { transform: translateY(-4px); opacity: 1; }
        }

        #sb-input-container {
            padding: 16px;
            border-top: 1px solid #e5e7eb;
            display: flex;
            gap: 10px;
        }

        #sb-input {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid #e5e7eb;
            border-radius: 24px;
            font-size: 14px;
            outline: none;
            font-family: inherit;
        }

        #sb-input:focus {
            border-color: var(--sb-primary);
        }

        #sb-send {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: var(--sb-primary);
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: opacity 0.2s;
        }

        #sb-send:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        #sb-send svg {
            width: 20px;
            height: 20px;
            fill: white;
        }

        @media (max-width: 480px) {
            #sb-container {
                bottom: 0;
                right: 0;
                width: 100%;
                max-width: 100%;
                height: 100%;
                max-height: 100%;
                border-radius: 0;
            }
            
            #sb-widget {
                bottom: 0;
                right: 0;
            }
        }
    `;

    // SVG Icons
    const ICONS = {
        chat: `<svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
        close: `<svg viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"/></svg>`,
        send: `<svg viewBox="0 0 24 24"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>`
    };

    // StudentBot class
    class StudentBot {
        constructor(config = {}) {
            this.config = { ...DEFAULT_CONFIG, ...config };
            this.sessionId = this._generateSessionId();
            this.isOpen = false;
            this.isTyping = false;
            
            this._init();
        }

        _generateSessionId() {
            let id = localStorage.getItem('sb_session_id');
            if (!id) {
                id = 'sb_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                localStorage.setItem('sb_session_id', id);
            }
            return id;
        }

        _init() {
            // Inject styles
            this._injectStyles();
            
            // Create widget DOM
            this._createWidget();
            
            // Bind events
            this._bindEvents();
        }

        _injectStyles() {
            if (document.getElementById('sb-styles')) return;
            
            const styleEl = document.createElement('style');
            styleEl.id = 'sb-styles';
            styleEl.textContent = STYLES;
            document.head.appendChild(styleEl);
            
            // Set CSS variables
            const root = document.documentElement;
            root.style.setProperty('--sb-primary-color', this.config.primaryColor);
            root.style.setProperty('--sb-bg-color', this.config.backgroundColor);
            root.style.setProperty('--sb-text-color', this.config.textColor);
            root.style.setProperty('--sb-font-family', this.config.fontFamily);
        }

        _createWidget() {
            const widget = document.createElement('div');
            widget.id = 'sb-widget';
            widget.innerHTML = `
                <div id="sb-container">
                    <div id="sb-header">
                        <div id="sb-header-avatar">AI</div>
                        <div id="sb-header-info">
                            <h3>${this.config.title}</h3>
                            <p>Online</p>
                        </div>
                    </div>
                    <div id="sb-messages">
                        <div class="sb-message sb-bot">
                            ${this.config.welcomeMessage}
                        </div>
                    </div>
                    <div id="sb-input-container">
                        <input type="text" id="sb-input" placeholder="Type your question..." autocomplete="off">
                        <button id="sb-send">${ICONS.send}</button>
                    </div>
                </div>
                <button id="sb-button">${ICONS.chat}</button>
            `;
            document.body.appendChild(widget);
            
            // Cache DOM elements
            this.button = document.getElementById('sb-button');
            this.container = document.getElementById('sb-container');
            this.messages = document.getElementById('sb-messages');
            this.input = document.getElementById('sb-input');
            this.sendBtn = document.getElementById('sb-send');
        }

        _bindEvents() {
            // Toggle widget
            this.button.addEventListener('click', () => this.toggle());
            
            // Send on button click
            this.sendBtn.addEventListener('click', () => this.send());
            
            // Send on Enter
            this.input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.send();
            });
        }

        toggle() {
            this.isOpen = !this.isOpen;
            this.container.classList.toggle('open', this.isOpen);
            this.button.innerHTML = this.isOpen ? ICONS.close : ICONS.chat;
            
            if (this.isOpen) {
                this.input.focus();
            }
        }

        async send() {
            const message = this.input.value.trim();
            if (!message || this.isTyping) return;

            // Add user message
            this._addMessage(message, 'user');
            this.input.value = '';

            // Show typing
            this._showTyping();

            try {
                const response = await fetch(this.config.apiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: message,
                        session_id: this.sessionId
                    })
                });

                const data = await response.json();
                this._hideTyping();
                this._addMessage(data.response, 'bot', data.confidence);

            } catch (error) {
                console.error('StudentBot error:', error);
                this._hideTyping();
                this._addMessage('Sorry, I\'m having trouble connecting. Please try again.', 'bot');
            }
        }

        _addMessage(text, sender, confidence = null) {
            // Remove welcome message if exists
            const welcomeMsg = this.messages.querySelector('.sb-bot');
            if (welcomeMsg && welcomeMsg.textContent === this.config.welcomeMessage) {
                welcomeMsg.remove();
            }

            const msg = document.createElement('div');
            msg.className = `sb-message sb-${sender}`;
            
            let content = `<p>${text}</p>`;
            if (confidence !== null && sender === 'bot') {
                const percent = Math.round(confidence * 100);
                content += `<small style="opacity:0.7">Confidence: ${percent}%</small>`;
            }
            
            msg.innerHTML = content;
            this.messages.appendChild(msg);
            this.messages.scrollTop = this.messages.scrollHeight;
        }

        _showTyping() {
            this.isTyping = true;
            this.sendBtn.disabled = true;
            
            const typing = document.createElement('div');
            typing.className = 'sb-message sb-bot sb-typing';
            typing.id = 'sb-typing';
            typing.innerHTML = '<span></span><span></span><span></span>';
            this.messages.appendChild(typing);
            this.messages.scrollTop = this.messages.scrollHeight;
        }

        _hideTyping() {
            this.isTyping = false;
            this.sendBtn.disabled = false;
            
            const typing = document.getElementById('sb-typing');
            if (typing) typing.remove();
        }
    }

    // Export to global
    window.StudentBot = {
        init: function(config) {
            return new StudentBot(config);
        }
    };

    // Auto-init if data attribute is present
    document.addEventListener('DOMContentLoaded', () => {
        const autoInit = document.querySelector('[data-student-bot]');
        if (autoInit) {
            const config = {};
            if (autoInit.dataset.apiUrl) config.apiUrl = autoInit.dataset.apiUrl;
            if (autoInit.dataset.title) config.title = autoInit.dataset.title;
            new StudentBot(config);
        }
    });

})();

