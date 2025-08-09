$(document).ready(function() {
    const chatMessages = $('#chat-messages');
    const chatForm = $('#chat-form');
    const userInput = $('#user-input');
    const clearChatBtn = $('#clear-chat-btn');
    const confirmationModal = $('#confirmation-modal');
    const confirmDeleteBtn = $('#confirm-delete-btn');
    const cancelDeleteBtn = $('#cancel-delete-btn');
    const webSearchToggle = $('#web-search-toggle');

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
        if(chatMessages.length) {
            chatMessages.scrollTop(chatMessages[0].scrollHeight);
        }
    }
    scrollToBottom();

    chatForm.on('submit', function(e) {
        e.preventDefault();
        const message = userInput.val().trim();
        if (!message) return;

        const searchWeb = webSearchToggle.is(':checked');

        appendMessage(message, 'user');
        userInput.val('');
        showTypingIndicator();

        fetch('/api/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ 
                message: message,
                search_web: searchWeb 
            })
        })
        .then(response => response.json())
        .then(data => {
            removeTypingIndicator();
            if (data.response) {
                appendMessage(data.response, 'bot');
            } else {
                appendMessage('Rất tiếc, đã có lỗi xảy ra.', 'bot');
            }
        })
        .catch(error => {
            removeTypingIndicator();
            console.error('Error:', error);
            appendMessage('Lỗi kết nối đến máy chủ.', 'bot');
        });
    });

    clearChatBtn.on('click', function() {
        confirmationModal.show();
    });

    cancelDeleteBtn.on('click', function() {
        confirmationModal.hide();
    });

    confirmDeleteBtn.on('click', function() {
        // SỬA LỖI: Sử dụng đúng đường dẫn API là '/api/chat/delete/'
        fetch('/api/chat/delete/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Thay vì thêm tin nhắn chào, ta tải lại trang để làm mới hoàn toàn
                window.location.reload();
            } else {
                alert('Lỗi: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Đã có lỗi xảy ra phía client.');
        })
        .finally(() => {
            confirmationModal.hide();
        });
    });

    function appendMessage(content, role) {
        const messageDiv = $('<div>').addClass('message').addClass(role === 'user' ? 'user-message' : 'bot-message');
        const avatarDiv = $('<div>').addClass('message-avatar');
        if (role === 'user') {
            avatarDiv.html('<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="#e0e0e0" viewBox="0 0 16 16"><path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6m2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0m4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4m-1-.004c-.001-.246-.154-.986-.832-1.664C11.516 10.68 10.289 10 8 10s-3.516.68-4.168 1.332c-.678.678-.83 1.418-.832 1.664z"/></svg>');
        } else {
            avatarDiv.html('<img src="https://res.cloudinary.com/dd7gti2kn/image/upload/v1752353858/Rita_logo__gjytjk.png" alt="Rita">');
        }
        const formattedContent = content.replace(/\n/g, '<br>');
        const contentDiv = $('<div>').addClass('message-content').html($('<p>').html(formattedContent));
        messageDiv.append(avatarDiv, contentDiv);
        chatMessages.append(messageDiv);
        scrollToBottom();
    }

    function showTypingIndicator() {
        const typingDiv = $('<div>').addClass('message bot-message typing-indicator').attr('id', 'typing-indicator');
        const avatarDiv = $('<div>').addClass('message-avatar').html('<img src="https://res.cloudinary.com/dd7gti2kn/image/upload/v1752353858/Rita_logo__gjytjk.png" alt="Rita">');
        const contentDiv = $('<div>').addClass('message-content').html('<p>Rita is typing<span>.</span><span>.</span><span>.</span></p>');
        typingDiv.append(avatarDiv, contentDiv);
        chatMessages.append(typingDiv);
        scrollToBottom();
    }

    function removeTypingIndicator() {
        $('#typing-indicator').remove();
    }
});
