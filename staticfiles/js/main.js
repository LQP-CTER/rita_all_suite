document.addEventListener('DOMContentLoaded', () => {
    const chatThread = document.getElementById('chat-container');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const refreshChatBtn = document.getElementById('refresh-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const fileInput = document.getElementById('file-input');
    const fileInfoContainer = document.getElementById('file-info-container');
    const promptChips = Array.from(document.querySelectorAll('.prompt-chip'));
    const searchWebToggle = document.getElementById('search-web-toggle');

    const MAX_FILES = 5;
    const MAX_FILE_SIZE_MB = 10;

    let attachedFiles = [];

    function syncSendButtonState() {
        if (!sendBtn || !userInput) return;
        sendBtn.disabled = userInput.value.trim().length === 0 && attachedFiles.length === 0;
    }

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
    
    function ensurePlaceholder() {
        if (chatThread && chatThread.children.length === 0) {
            chatThread.innerHTML = `
                <div class="chat-placeholder">
                    <img src="https://res.cloudinary.com/dd7gti2kn/image/upload/v1752353858/Rita_logo__gjytjk.png" alt="Rita Logo" class="placeholder-logo">
                    <h2>How can I help you today?</h2>
                </div>`;
        } else if (chatThread) {
             const placeholder = chatThread.querySelector('.chat-placeholder');
             if (placeholder) placeholder.remove();
        }
    }

    function addMessageToUI({ role, content, isThinking = false }) {
        if (!chatThread) return null;
        ensurePlaceholder();

        const messageClass = role === 'user' ? 'user' : 'rita';
        const avatarHTML = role === 'user'
            ? `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="#e0e0e0" viewBox="0 0 16 16"><path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6m2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0m4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4m-1-.004c-.001-.246-.154-.986-.832-1.664C11.516 10.68 10.289 10 8 10s-3.516.68-4.168 1.332c-.678.678-.83 1.418-.832 1.664z"/></svg>`
            : `<img src="https://res.cloudinary.com/dd7gti2kn/image/upload/v1752353858/Rita_logo__gjytjk.png" alt="Rita">`;
        
        const thinkingClass = isThinking ? 'thinking' : '';
        const messageEl = document.createElement('div');
        messageEl.className = `message ${messageClass}`;
        if (isThinking) {
            messageEl.id = 'thinking-indicator';
        }
        
        messageEl.innerHTML = `
            <div class="message-avatar">${avatarHTML}</div>
            <div class="message-content ${thinkingClass}">
                <p>${content.replace(/\n/g, '<br>')}</p>
            </div>`;
            
        chatThread.appendChild(messageEl);
        scrollToBottom();
        return messageEl;
    }
    
    function updateFileInfoUI() {
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
                updateFileInfoUI();
                syncSendButtonState();
            };
            item.appendChild(removeBtn);
            fileInfoContainer.appendChild(item);
        });
    }

    function validateAndStoreFiles(files) {
        let newFiles = Array.from(files);

        if (attachedFiles.length + newFiles.length > MAX_FILES) {
            alert(`You can only upload a maximum of ${MAX_FILES} files.`);
            return;
        }

        for (const file of newFiles) {
            if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
                alert(`File "${file.name}" exceeds the ${MAX_FILE_SIZE_MB}MB size limit.`);
                return;
            }
        }
        
        attachedFiles.push(...newFiles);
        updateFileInfoUI();
        syncSendButtonState();
    }


    async function handleFormSubmit(event) {
        event.preventDefault();
        const message = userInput.value.trim();
        if (!message && attachedFiles.length === 0) return;

        const userMessageContent = message || `Đã gửi ${attachedFiles.length} tệp.`;
        addMessageToUI({ role: 'user', content: escapeHTML(userMessageContent) });

        const formData = new FormData();
        formData.append('message', message);
        formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
        if (searchWebToggle) {
            formData.append('search_web', searchWebToggle.checked);
        }
        attachedFiles.forEach(file => formData.append('files', file));
        
        userInput.value = '';
        userInput.dispatchEvent(new Event('input'));
        attachedFiles = [];
        updateFileInfoUI();
        syncSendButtonState();

        const thinkingIndicator = addMessageToUI({ role: 'assistant', content: 'Rita is thinking...', isThinking: true });

        try {
            const response = await fetch('/api/chat/', {
                method: 'POST',
                body: formData
            });

            if (thinkingIndicator) thinkingIndicator.remove();
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'An unknown server error occurred.' }));
                throw new Error(errorData.error || `Server responded with status ${response.status}`);
            }
            
            const data = await response.json();
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

            if (!response.ok) {
                 const errorData = await response.json().catch(() => ({ message: 'Failed to refresh chat.' }));
                 throw new Error(errorData.message);
            }

            const data = await response.json();
            if (data.status !== 'success') {
                throw new Error(data.message || 'Failed to refresh chat.');
            }

            if (chatThread) {
                chatThread.innerHTML = '';
                ensurePlaceholder();
            }
            if (userInput) userInput.focus();

        } catch (error) {
            console.error('Error refreshing chat:', error);
            alert(`Could not refresh chat: ${error.message}`);
        }
    }

    if (chatForm) {
        chatForm.addEventListener('submit', handleFormSubmit);
    }

    if (refreshChatBtn) {
        refreshChatBtn.addEventListener('click', handleRefreshChat);
    }

    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', () => {
            validateAndStoreFiles(fileInput.files);
            fileInput.value = '';
        });
    }

    if (userInput && sendBtn) {
        userInput.addEventListener('input', () => {
            userInput.style.height = 'auto';
            userInput.style.height = `${userInput.scrollHeight}px`;
            syncSendButtonState();
        });

        userInput.addEventListener('keydown', event => {
            if (event.key === 'Enter' && !event.shiftKey && !sendBtn.disabled) {
                event.preventDefault();
                chatForm.requestSubmit();
            }
        });
    }

    if (promptChips.length && userInput) {
        promptChips.forEach(chip => {
            chip.addEventListener('click', () => {
                const prompt = chip.dataset.prompt || chip.textContent.trim();
                userInput.value = prompt;
                userInput.focus();
                userInput.dispatchEvent(new Event('input'));
            });
        });
    }

    ensurePlaceholder();
    scrollToBottom();
    if (userInput) {
        userInput.dispatchEvent(new Event('input'));
    }
});