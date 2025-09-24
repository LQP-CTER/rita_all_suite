// static/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    // --- Start: Custom Modal Implementation ---
    // This replaces the browser's default alert() and confirm() dialogs.
    function addModalStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .rita-modal-overlay {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background-color: rgba(0, 0, 0, 0.6); display: flex;
                justify-content: center; align-items: center; z-index: 1050;
                opacity: 0; transition: opacity 0.2s ease-in-out;
            }
            .rita-modal-overlay.visible { opacity: 1; }
            .rita-modal-box {
                background: #fff; color: #333; padding: 25px; border-radius: 8px;
                width: 90%; max-width: 400px; text-align: center;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
                transform: scale(0.9); transition: transform 0.2s ease-in-out;
            }
            .rita-modal-overlay.visible .rita-modal-box { transform: scale(1); }
            .rita-modal-box p { margin: 0 0 20px; font-size: 1rem; line-height: 1.5; }
            .rita-modal-buttons { display: flex; justify-content: center; gap: 15px; }
            .rita-modal-box button {
                padding: 10px 22px; border-radius: 5px; border: none;
                cursor: pointer; font-weight: bold; transition: background-color 0.2s;
            }
            .rita-modal-confirm-btn { background-color: #007bff; color: white; }
            .rita-modal-confirm-btn:hover { background-color: #0056b3; }
            .rita-modal-cancel-btn, .rita-modal-ok-btn { background-color: #6c757d; color: white; }
            .rita-modal-cancel-btn:hover, .rita-modal-ok-btn:hover { background-color: #5a6268; }
        `;
        document.head.appendChild(style);
    }

    function showCustomAlert(message, callback) {
        const modalOverlay = document.createElement('div');
        modalOverlay.className = 'rita-modal-overlay';
        modalOverlay.innerHTML = `
            <div class="rita-modal-box">
                <p>${message}</p>
                <div class="rita-modal-buttons">
                    <button class="rita-modal-ok-btn">OK</button>
                </div>
            </div>
        `;
        document.body.appendChild(modalOverlay);
        setTimeout(() => modalOverlay.classList.add('visible'), 10);
        modalOverlay.querySelector('.rita-modal-ok-btn').onclick = () => {
            modalOverlay.classList.remove('visible');
            modalOverlay.addEventListener('transitionend', () => {
                document.body.removeChild(modalOverlay);
                if (callback) callback();
            }, { once: true });
        };
    }

    function showCustomConfirm(message, onConfirm) {
        const modalOverlay = document.createElement('div');
        modalOverlay.className = 'rita-modal-overlay';
        modalOverlay.innerHTML = `
            <div class="rita-modal-box">
                <p>${message}</p>
                <div class="rita-modal-buttons">
                    <button class="rita-modal-confirm-btn">Confirm</button>
                    <button class="rita-modal-cancel-btn">Cancel</button>
                </div>
            </div>
        `;
        document.body.appendChild(modalOverlay);
        setTimeout(() => modalOverlay.classList.add('visible'), 10);
        const close = () => {
            modalOverlay.classList.remove('visible');
            modalOverlay.addEventListener('transitionend', () => document.body.removeChild(modalOverlay), { once: true });
        };
        modalOverlay.querySelector('.rita-modal-confirm-btn').onclick = () => { close(); onConfirm(true); };
        modalOverlay.querySelector('.rita-modal-cancel-btn').onclick = () => { close(); onConfirm(false); };
    }

    addModalStyles();
    // --- End: Custom Modal Implementation ---

    // --- DOM Elements (from old file, with additions) ---
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input'); // Using old ID
    const sendBtn = document.getElementById('send-btn'); // Using old ID
    const uploadBtn = document.getElementById('upload-btn'); // Using old ID
    const fileInput = document.getElementById('file-input');
    const filePreviewContainer = document.getElementById('file-info-container'); // Using old ID
    const refreshChatBtn = document.getElementById('refresh-chat-btn'); // New element from newer version

    // --- Helper Functions ---
    function scrollToBottom() {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // --- NEW File Handling Logic (replaces old `attachedFiles` array) ---
    if (fileInput && filePreviewContainer) {
        fileInput.addEventListener('change', function() {
            filePreviewContainer.innerHTML = ''; // Clear previous previews
            if (this.files.length > 0) {
                filePreviewContainer.style.display = 'flex'; // Show container
                Array.from(this.files).forEach(file => {
                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-info-item'; // Use old class name
                    
                    const fileName = document.createElement('span');
                    fileName.textContent = file.name;
                    
                    const removeBtn = document.createElement('span');
                    removeBtn.className = 'remove-file-btn';
                    removeBtn.innerHTML = '&times;';
                    
                    removeBtn.onclick = function() {
                        const newFiles = new DataTransfer();
                        Array.from(fileInput.files).forEach(f => {
                            if (f !== file) newFiles.items.add(f);
                        });
                        fileInput.files = newFiles.files;
                        fileInput.dispatchEvent(new Event('change')); // Re-render previews
                    };

                    fileItem.appendChild(fileName);
                    fileItem.appendChild(removeBtn);
                    filePreviewContainer.appendChild(fileItem);
                });
            } else {
                 filePreviewContainer.style.display = 'none'; // Hide if no files
            }
            sendBtn.disabled = userInput.value.trim().length === 0 && this.files.length === 0;
        });
    }

    // --- Core Chat Functions (from old file, improved) ---
    function appendMessage(content, role) {
        if (!chatMessages) return;
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', role === 'user' ? 'user-message' : 'bot-message');

        const avatarSrc = role === 'user' 
            ? `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="#e0e0e0" viewBox="0 0 16 16"><path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6m2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0m4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4m-1-.004c-.001-.246-.154-.986-.832-1.664C11.516 10.68 10.289 10 8 10s-3.516.68-4.168 1.332c-.678.678-.83 1.418-.832 1.664z"/></svg>`
            : `<img src="https://res.cloudinary.com/dd7gti2kn/image/upload/v1752353858/Rita_logo__gjytjk.png" alt="Rita">`;
        
        let fileContentHTML = '';
        if (role === 'user' && fileInput && fileInput.files.length > 0) {
            const fileNames = Array.from(fileInput.files).map(f => f.name).join(', ');
            fileContentHTML = `<div class="message-files"><strong>Đính kèm:</strong> ${fileNames}</div>`;
        }

        messageDiv.innerHTML = `
            <div class="message-avatar">${avatarSrc}</div>
            <div class="message-content">
                ${content.replace(/\n/g, '<br>')}
                ${fileContentHTML}
            </div>
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
            <div class="message-content">Rita is typing...</div>
        `;
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.remove();
    }

    async function handleFormSubmit(e) {
        e.preventDefault();
        const message = userInput.value.trim();
        const files = fileInput ? fileInput.files : [];

        if (!message && files.length === 0) return;

        appendMessage(message || ' ', 'user');
        
        const formData = new FormData();
        formData.append('message', message);
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) {
            formData.append('csrfmiddlewaretoken', csrfToken.value);
        }
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }

        userInput.value = '';
        userInput.style.height = 'auto';
        userInput.focus();
        if (fileInput) fileInput.value = '';
        if (filePreviewContainer) {
            filePreviewContainer.innerHTML = '';
            filePreviewContainer.style.display = 'none';
        }
        sendBtn.disabled = true;

        showTypingIndicator();

        try {
            const response = await fetch(chatForm.action || '/api/chat/', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            removeTypingIndicator();
            appendMessage(data.response || data.error || 'Rất tiếc, đã có lỗi xảy ra.', 'bot');

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
            sendBtn.disabled = userInput.value.trim().length === 0 && (!fileInput || fileInput.files.length === 0);
        });

        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!sendBtn.disabled) {
                     chatForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
                }
            }
        });
    }

    if (uploadBtn) {
        uploadBtn.addEventListener('click', () => fileInput.click());
    }

    if (refreshChatBtn) {
        refreshChatBtn.addEventListener('click', function() {
            showCustomConfirm('Bạn có chắc muốn xóa toàn bộ lịch sử trò chuyện không?', (confirmed) => {
                if (confirmed) {
                    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
                    fetch(refreshChatBtn.dataset.url, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken ? csrfToken.value : '',
                            'Content-Type': 'application/json'
                        },
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            if(chatMessages) chatMessages.innerHTML = '';
                            appendMessage('Xin chào! Tôi là Rita, trợ lý AI của bạn. Bạn cần giúp gì hôm nay?', 'bot');
                        }
                        showCustomAlert(data.message || 'Có lỗi xảy ra.');
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showCustomAlert('Đã xảy ra lỗi khi làm mới cuộc trò chuyện.');
                    });
                }
            });
        });
    }

    // --- Initial Setup ---
    if (chatMessages && chatMessages.children.length === 0) {
        appendMessage('Xin chào! Tôi là Rita, trợ lý AI của bạn. Bạn cần giúp gì hôm nay?', 'bot');
    }
    scrollToBottom();
    if(userInput) {
        userInput.focus();
        sendBtn.disabled = userInput.value.trim().length === 0 && (!fileInput || fileInput.files.length === 0);
    }
});