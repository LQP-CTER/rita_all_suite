document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Nodes ---
    const chatThread = document.getElementById('chat-container');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const refreshChatBtn = document.getElementById('refresh-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const fileInput = document.getElementById('file-input');
    const fileInfoContainer = document.getElementById('file-info-container');

    let attachedFiles = [];

    // --- Helpers ---
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
        if (chatThread) {
            chatThread.scrollTop = chatThread.scrollHeight;
        }
    }

    function escapeHTML(str) {
        const p = document.createElement("p");
        p.textContent = str;
        return p.innerHTML;
    }
    
    function addMessageToUI({ role, content, isThinking = false }) {
        if (!chatThread) return null;

        const messageClass = role === 'user' ? 'user' : 'rita';
        const avatarHTML = role === 'user'
            ? `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="#e0e0e0" viewBox="0 0 16 16"><path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6m2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0m4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4m-1-.004c-.001-.246-.154-.986-.832-1.664C11.516 10.68 10.289 10 8 10s-3.516.68-4.168 1.332c-.678.678-.83 1.418-.832 1.664z"/></svg>`
            : `<img src="https://res.cloudinary.com/dd7gti2kn/image/upload/v1752353858/Rita_logo__gjytjk.png" alt="Rita">`;
        
        const messageEl = document.createElement('div');
        messageEl.className = `message ${messageClass}`;
        if (isThinking) {
            messageEl.id = 'thinking-indicator';
        }
        
        messageEl.innerHTML = `
            <div class="message-avatar">${avatarHTML}</div>
            <div class="message-content">
                <p>${content.replace(/\n/g, '<br>')}</p>
            </div>`;
            
        chatThread.appendChild(messageEl);
        scrollToBottom();
        return messageEl;
    }
    
    function updateFileInput() {
        if (!fileInfoContainer) return;
        
        fileInfoContainer.innerHTML = '';
        if (attachedFiles.length === 0) {
            fileInfoContainer.style.display = 'none';
        } else {
            fileInfoContainer.style.display = 'flex';
        }

        attachedFiles.forEach((file, index) => {
            const item = document.createElement('div');
            item.className = 'file-info-item';
            
            const nameSpan = document.createElement('span');
            nameSpan.textContent = file.name;
            item.appendChild(nameSpan);
            
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'remove-file-btn';
            removeBtn.innerHTML = '&times;';
            removeBtn.title = 'Remove file';
            removeBtn.onclick = () => {
                attachedFiles.splice(index, 1);
                updateFileInput();
            };
            item.appendChild(removeBtn);
            fileInfoContainer.appendChild(item);
        });
        
        // Update send button state
        sendBtn.disabled = userInput.value.trim().length === 0 && attachedFiles.length === 0;
    }

    // --- Main Logic ---
    async function handleFormSubmit(event) {
        event.preventDefault();
        const message = userInput.value.trim();
        if (!message && attachedFiles.length === 0) return;

        const userMessageContent = message || `Đã gửi ${attachedFiles.length} tệp.`;
        addMessageToUI({ role: 'user', content: escapeHTML(userMessageContent) });

        const formData = new FormData();
        formData.append('message', message);
        formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
        attachedFiles.forEach(file => formData.append('files', file));
        
        // Clear input fields after preparing FormData
        userInput.value = '';
        userInput.dispatchEvent(new Event('input')); // To resize textarea and update button state
        attachedFiles = [];
        updateFileInput();

        const thinkingIndicator = addMessageToUI({ role: 'assistant', content: 'Rita is thinking...', isThinking: true });

        try {
            const response = await fetch('/api/chat/', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (thinkingIndicator) thinkingIndicator.remove();

            if (!response.ok || data.error) {
                throw new Error(data.error || 'An unknown server error occurred.');
            }
            
            addMessageToUI({role: 'assistant', content: data.answer || "Sorry, I couldn't get a response."});

        } catch (error) {
            console.error('Error sending message:', error);
            if(thinkingIndicator) thinkingIndicator.remove();
            addMessageToUI({role: 'assistant', content: `Sorry, an error occurred: ${error.message}`});
        }
    }

    async function handleRefreshChat() {
        const confirmed = confirm('Bạn có chắc muốn bắt đầu một cuộc trò chuyện mới? Toàn bộ nội dung sẽ bị xóa.');
        if (!confirmed) return;

        try {
            const response = await fetch('/api/chat/refresh/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            if (!response.ok || data.status !== 'success') {
                throw new Error(data.message || 'Failed to refresh chat.');
            }

            if (chatThread) {
                chatThread.innerHTML = ''; // Clear current chat
                addMessageToUI({ role: 'assistant', content: 'Hello! I am Rita, your personal AI assistant. How can I help you today?' });
            }
            if (userInput) userInput.focus();

        } catch (error) {
            console.error('Error refreshing chat:', error);
            alert(`Could not refresh chat: ${error.message}`);
        }
    }

    // --- Event Bindings ---
    if (chatForm) chatForm.addEventListener('submit', handleFormSubmit);
    if (refreshChatBtn) refreshChatBtn.addEventListener('click', handleRefreshChat);

    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', () => {
            attachedFiles.push(...Array.from(fileInput.files));
            updateFileInput();
            fileInput.value = ''; // Reset for re-uploading the same file
        });
    }

    if (userInput && sendBtn) {
        userInput.addEventListener('input', () => {
            userInput.style.height = 'auto';
            userInput.style.height = `${userInput.scrollHeight}px`;
            sendBtn.disabled = userInput.value.trim().length === 0 && attachedFiles.length === 0;
        });

        userInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey && !sendBtn.disabled) {
                event.preventDefault();
                chatForm.requestSubmit();
            }
        });
    }

    // --- Initial setup ---
    scrollToBottom();
    if (userInput) {
        userInput.focus();
        userInput.dispatchEvent(new Event('input')); // Initial check for button state
    }
});