document.addEventListener('DOMContentLoaded', function () {

    // --- Hàm tiện ích ---
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

    function formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
        return num;
    }

    // --- Chức năng chính: Phân tích Video ---
    const analyzeForm = document.getElementById('analyze-form');
    if (analyzeForm) {
        const urlInput = document.getElementById('tiktok-url-input');
        const analyzeBtn = document.getElementById('analyze-btn');
        const loadingIndicator = document.getElementById('loading-indicator');
        const resultsWrapper = document.getElementById('results-wrapper');
        const videoCover = document.getElementById('video-cover');
        const videoTitle = document.getElementById('video-title');
        const videoAuthor = document.getElementById('video-author');
        const videoDownloadLink = document.getElementById('video-download-link');
        const transcriptOutput = document.getElementById('transcript-output');
        const analysisOutput = document.getElementById('analysis-output');
        const playCountEl = document.getElementById('play-count');
        const likeCountEl = document.getElementById('like-count');
        const commentCountEl = document.getElementById('comment-count');
        const shareCountEl = document.getElementById('share-count');
        const historyList = document.getElementById('history-list');
        
        let pollingInterval;

        function pollForAnalysis(videoId) {
            pollingInterval = setInterval(async () => {
                try {
                    const response = await fetch(`/api/tiktok-analyzer/status/?id=${videoId}`);
                    const data = await response.json();

                    if (data.status === 'COMPLETE') {
                        clearInterval(pollingInterval);
                        displayAnalysis(data.analysis);
                    } else if (data.status === 'FAILED') {
                        clearInterval(pollingInterval);
                        analysisOutput.innerHTML = '<p class="error" style="color: #e53e3e;">Quá trình phân tích AI đã thất bại. Vui lòng thử lại.</p>';
                    }
                } catch (error) {
                    clearInterval(pollingInterval);
                    console.error('Lỗi khi kiểm tra trạng thái:', error);
                }
            }, 5000); // Kiểm tra mỗi 5 giây
        }
        
        function displayAnalysis(analysisData) {
            analysisOutput.innerHTML = ''; // Xóa trạng thái "Đang phân tích"
            if (typeof analysisData === 'object' && analysisData !== null) {
                const summaryTitle = document.createElement('h4');
                summaryTitle.textContent = 'Tóm tắt';
                const summaryText = document.createElement('p');
                summaryText.textContent = analysisData.summary || 'Không có tóm tắt.';
                analysisOutput.appendChild(summaryTitle);
                analysisOutput.appendChild(summaryText);

                if (analysisData.main_topics && analysisData.main_topics.length > 0) {
                    const topicsTitle = document.createElement('h4');
                    topicsTitle.textContent = 'Chủ đề chính';
                    const topicsList = document.createElement('ul');
                    topicsList.className = 'topics-list';
                    analysisData.main_topics.forEach(topic => {
                        const topicItem = document.createElement('li');
                        topicItem.textContent = topic;
                        topicsList.appendChild(topicItem);
                    });
                    analysisOutput.appendChild(topicsTitle);
                    analysisOutput.appendChild(topicsList);
                }
            } else {
                 analysisOutput.textContent = 'Không có dữ liệu phân tích.';
            }
        }

        function addVideoToHistory(videoData, originalUrl) {
            const noHistoryMsg = document.getElementById('no-history-msg');
            if (noHistoryMsg) {
                noHistoryMsg.remove();
            }
            const card = document.createElement('div');
            card.className = 'history-card';
            card.dataset.id = videoData.id;
            const description = videoData.description && videoData.description.length > 80 
                ? videoData.description.substring(0, 80) + '...' 
                : videoData.description;

            card.innerHTML = `
                <input type="checkbox" class="history-checkbox" style="display: none;">
                <img src="${videoData.cover_url}" alt="Video cover" class="history-card-cover" onerror="this.src='https://placehold.co/400/1e1e2f/e0e0e0?text=No+Cover'">
                <div class="history-card-body">
                    <p class="history-card-desc">${description || 'Không có mô tả'}</p>
                    <p class="history-card-author">bởi @${videoData.author}</p>
                    <div class="history-card-footer">
                        <small class="history-card-date">Vừa xong</small>
                        <a href="${originalUrl}" target="_blank" rel="noopener noreferrer" class="history-card-link">Xem lại</a>
                    </div>
                </div>
            `;
            historyList.prepend(card);
            card.addEventListener('click', handleCardClick);
        }

        async function handleAnalysis(event) {
            event.preventDefault();
            const videoUrl = urlInput.value.trim();
            if (!videoUrl) {
                alert('Vui lòng nhập đường dẫn video TikTok.');
                return;
            }

            if (pollingInterval) clearInterval(pollingInterval);

            resultsWrapper.style.display = 'none';
            loadingIndicator.style.display = 'block';
            analyzeBtn.disabled = true;
            analyzeBtn.textContent = 'Đang lấy thông tin...';

            try {
                const response = await fetch('/api/tiktok-analyzer/submit/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                    body: JSON.stringify({ video_url: videoUrl })
                });
                const data = await response.json();

                loadingIndicator.style.display = 'none';

                if (response.ok && data.status === 'processing') {
                    const video = data.video;
                    
                    videoCover.src = video.cover_url || 'https://placehold.co/600x400/1e1e2f/e0e0e0?text=No+Cover';
                    videoTitle.textContent = video.description || 'Không có tiêu đề';
                    videoAuthor.textContent = `Tác giả: @${video.author}`;
                    if (video.download_url) {
                        videoDownloadLink.href = video.download_url;
                        videoDownloadLink.style.display = 'block';
                    } else {
                        videoDownloadLink.style.display = 'none';
                    }
                    playCountEl.textContent = formatNumber(video.plays || 0);
                    likeCountEl.textContent = formatNumber(video.likes || 0);
                    commentCountEl.textContent = formatNumber(video.comments || 0);
                    shareCountEl.textContent = formatNumber(video.shares || 0);
                    transcriptOutput.textContent = video.transcript || 'Không có bản ghi.';
                    
                    analysisOutput.innerHTML = '<div class="spinner" style="width: 20px; height: 20px; border-width: 3px;"></div><p style="margin-top: 1rem;">Đang phân tích AI, vui lòng chờ...</p>';
                    resultsWrapper.style.display = 'block';

                    pollForAnalysis(video.id);
                    addVideoToHistory(video, videoUrl);

                } else {
                    alert(data.error || 'Lỗi không xác định.');
                }
            } catch (error) {
                console.error('Fetch Error:', error);
                alert('Không thể kết nối đến server.');
            } finally {
                analyzeBtn.disabled = false;
                analyzeBtn.textContent = 'Lấy thông tin';
            }
        }
        analyzeForm.addEventListener('submit', handleAnalysis);
    }

    // --- Chức năng: Xóa Lịch sử ---
    const selectBtn = document.getElementById('select-history-btn');
    const deleteBtn = document.getElementById('delete-selected-btn');
    const cancelBtn = document.getElementById('cancel-selection-btn');
    const allHistoryCards = document.querySelectorAll('.history-card');

    if (selectBtn && deleteBtn && cancelBtn) {
        let isInSelectionMode = false;
        let selectedIds = new Set();

        function toggleSelectionMode(enable) {
            isInSelectionMode = enable;
            selectBtn.style.display = enable ? 'none' : 'inline-block';
            deleteBtn.style.display = enable ? 'inline-block' : 'none';
            cancelBtn.style.display = enable ? 'inline-block' : 'none';

            document.querySelectorAll('.history-card').forEach(card => {
                const checkbox = card.querySelector('.history-checkbox');
                if(checkbox) checkbox.style.display = enable ? 'block' : 'none';
                card.classList.toggle('is-selecting', enable);
                if (!enable) {
                    card.classList.remove('is-selected');
                    if(checkbox) checkbox.checked = false;
                }
            });
            if (!enable) {
                selectedIds.clear();
            }
        }

        function handleCardClick(event) {
            if (!isInSelectionMode) return;
            const card = event.currentTarget;
            const checkbox = card.querySelector('.history-checkbox');
            const videoId = card.dataset.id;
            if (!checkbox || !videoId) return;

            if (event.target !== checkbox) {
                checkbox.checked = !checkbox.checked;
            }
            card.classList.toggle('is-selected', checkbox.checked);
            if (checkbox.checked) {
                selectedIds.add(videoId);
            } else {
                selectedIds.delete(videoId);
            }
        }

        async function deleteSelectedHistory() {
            const idsToDelete = Array.from(selectedIds);
            if (idsToDelete.length === 0) {
                alert('Vui lòng chọn ít nhất một mục để xóa.');
                return;
            }
            if (!confirm(`Bạn có chắc muốn xóa ${idsToDelete.length} mục đã chọn?`)) {
                return;
            }
            try {
                const response = await fetch('/api/tiktok-history/delete/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                    body: JSON.stringify({ ids: idsToDelete })
                });
                const data = await response.json();
                if (response.ok && data.status === 'success') {
                    idsToDelete.forEach(id => {
                        const card_to_delete = document.querySelector(`.history-card[data-id="${id}"]`);
                        if(card_to_delete) card_to_delete.remove();
                    });
                    alert(data.message);
                    toggleSelectionMode(false);
                } else {
                    alert(data.error || 'Đã có lỗi xảy ra.');
                }
            } catch (error) {
                console.error('Lỗi khi xóa:', error);
                alert('Không thể kết nối đến máy chủ.');
            }
        }

        selectBtn.addEventListener('click', () => toggleSelectionMode(true));
        cancelBtn.addEventListener('click', () => toggleSelectionMode(false));
        deleteBtn.addEventListener('click', deleteSelectedHistory);
        allHistoryCards.forEach(card => {
            card.addEventListener('click', handleCardClick);
        });
    }
});
