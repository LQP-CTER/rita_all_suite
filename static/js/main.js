// File: Rita_All_Django/static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // --- DOM Elements ---
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const fileInput = document.getElementById('file-input');
    const fileInfoContainer = document.getElementById('file-info-container');
    
    let attachedFiles = [];

    // --- Helper Functions ---
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function scrollToBottom() {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // --- File Handling Functions ---
    function updateFileInput() {
        if (attachedFiles.length === 0) {
            fileInfoContainer.innerHTML = '';
            fileInfoContainer.style.display = 'none';
            sendBtn.disabled = userInput.value.trim().length === 0;
            return;
        }

        fileInfoContainer.style.display = 'flex';
        fileInfoContainer.innerHTML = '';
        attachedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.classList.add('file-info-item');
            fileItem.innerHTML = `
                <span>${file.name}</span>
                <span class="remove-file-btn" data-index="${index}">&times;</span>
            `;
            fileInfoContainer.appendChild(fileItem);
        });

        // Add event listeners to remove buttons
        document.querySelectorAll('.remove-file-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const indexToRemove = parseInt(e.target.dataset.index, 10);
                attachedFiles.splice(indexToRemove, 1);
                updateFileInput();
            });
        });
        
        sendBtn.disabled = false;
    }

    // --- Core Chat Functions ---
    function appendMessage(content, role) {
        if (!chatMessages) return;
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', role === 'user' ? 'user-message' : 'bot-message');

        const avatarSrc = role === 'user' 
            ? `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="#e0e0e0" viewBox="0 0 16 16"><path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6m2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0m4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4m-1-.004c-.001-.246-.154-.986-.832-1.664C11.516 10.68 10.289 10 8 10s-3.516.68-4.168 1.332c-.678.678-.83 1.418-.832 1.664z"/></svg>`
            : `<img src="https://res.cloudinary.com/dd7gti2kn/image/upload/v1752353858/Rita_logo__gjytjk.png" alt="Rita">`;
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatarSrc}</div>
            <div class="message-content">${content.replace(/\n/g, '<br>')}</div>
        `;
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.classList.add('message', 'bot-message');
        typingDiv.innerHTML = `
            <div class="message-avatar">
                <img src="https://res.cloudinary.com/dd7gti2kn/image/upload/v1752353858/Rita_logo__gjytjk.png" alt="Rita">
            </div>
            <div class="message-content">
                Rita is typing...
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    async function handleFormSubmit(e) {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message && attachedFiles.length === 0) return;

        appendMessage(message || 'Đã gửi file...', 'user');
        
        const formData = new FormData();
        formData.append('message', message);
        formData.append('search_web', true);
        formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
        attachedFiles.forEach(file => {
            formData.append('files', file);
        });

        // Reset UI
        userInput.value = '';
        userInput.style.height = 'auto';
        userInput.focus();
        sendBtn.disabled = true;
        attachedFiles = [];
        updateFileInput();

        showTypingIndicator();

        try {
            const response = await fetch('/api/chat/', {
                method: 'POST',
                body: formData // No Content-Type header needed for FormData
            });
            const data = await response.json();
            
            removeTypingIndicator();

            if (data.response) {
                appendMessage(data.response, 'bot');
            } else {
                appendMessage(data.error || 'Rất tiếc, đã có lỗi xảy ra.', 'bot');
            }
        } catch (error) {
            removeTypingIndicator();
            console.error('Error:', error);
            appendMessage('Lỗi kết nối đến máy chủ.', 'bot');
        }
    }

    // --- Event Listeners ---
    if (chatForm) {
        chatForm.addEventListener('submit', handleFormSubmit);
    }
    
    if (userInput) {
        userInput.addEventListener('input', () => {
            userInput.style.height = 'auto';
            userInput.style.height = (userInput.scrollHeight) + 'px';
            sendBtn.disabled = userInput.value.trim().length === 0 && attachedFiles.length === 0;
        });

        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!sendBtn.disabled) {
                    chatForm.requestSubmit();
                }
            }
        });
    }

    if (uploadBtn) {
        uploadBtn.addEventListener('click', () => fileInput.click());
    }

    if (fileInput) {
        fileInput.addEventListener('change', () => {
            attachedFiles = [...attachedFiles, ...fileInput.files];
            updateFileInput();
            fileInput.value = ''; // Reset to allow re-selecting same file
        });
    }

    // --- Initial Setup ---
    if (chatMessages && chatMessages.children.length === 0) {
        appendMessage('Xin chào! Tôi là Rita, trợ lý AI của bạn. Bạn cần giúp gì hôm nay?', 'bot');
    }
    scrollToBottom();
    if(userInput) userInput.focus();
});