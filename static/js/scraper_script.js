// static/js/scraper_script.js

document.addEventListener('DOMContentLoaded', function () {
    // --- Lấy các element từ DOM ---
    const scrapeForm = document.getElementById('scrape-form');
    const urlInput = document.getElementById('url-input');
    const modelSelection = document.getElementById('model-selection');
    const startScrapeBtn = document.getElementById('start-scrape-btn');
    
    const resultsPlaceholder = document.getElementById('results-placeholder');
    const loadingIndicator = document.getElementById('loading-indicator');
    const resultsOutput = document.getElementById('results-output');
    
    const usageCard = document.getElementById('usage-card');
    const inputTokensEl = document.getElementById('input-tokens');
    const outputTokensEl = document.getElementById('output-tokens');
    const totalCostEl = document.getElementById('total-cost');
    
    const downloadJsonBtn = document.getElementById('download-json-btn');
    const downloadCsvBtn = document.getElementById('download-csv-btn');
    
    const historyTableBody = document.querySelector('#history-table tbody');
    const deleteHistoryBtn = document.getElementById('delete-history-btn');

    let pollingInterval;
    let tags = []; // Mảng để lưu trữ các trường cần lấy

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
    
    // --- Logic xử lý tag input ---
    const tagsContainer = document.getElementById('tags-input-container');
    const tagsInput = document.getElementById('fields-input');

    function createTag(label) {
        const div = document.createElement('div');
        div.setAttribute('class', 'tag-item');
        const span = document.createElement('span');
        span.innerHTML = label;
        const closeBtn = document.createElement('span');
        closeBtn.setAttribute('class', 'tag-remove');
        closeBtn.innerHTML = '&times;';
        closeBtn.onclick = () => {
            const index = tags.indexOf(label);
            tags.splice(index, 1);
            renderTags();
        };
        div.appendChild(span);
        div.appendChild(closeBtn);
        return div;
    }

    function renderTags() {
        if (!tagsContainer || !tagsInput) return;
        document.querySelectorAll('.tag-item').forEach(tag => tag.remove());
        tagsContainer.appendChild(tagsInput);
        tags.slice().reverse().forEach(tag => {
            tagsContainer.prepend(createTag(tag));
        });
    }

    if(tagsInput) {
        tagsInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                const tagLabel = tagsInput.value.trim();
                if (tagLabel && !tags.includes(tagLabel)) {
                    tags.push(tagLabel);
                    renderTags();
                }
                tagsInput.value = '';
            } else if (event.key === 'Backspace' && tagsInput.value === '' && tags.length > 0) {
                tags.pop();
                renderTags();
            }
        });
    }

    // --- Xử lý form submit ---
    if(scrapeForm) {
        console.log("Scraper script loaded and form found. Attaching submit listener."); // DEBUG
        scrapeForm.addEventListener('submit', async function(e) {
            console.log("Submit button clicked, form event captured."); // DEBUG
            e.preventDefault(); // Ngăn chặn hành vi mặc định của form
            
            const url = urlInput.value.trim();
            const model = modelSelection.value;
            const fields = tags.join(',');

            if (!url || !fields) {
                alert('Vui lòng nhập URL và ít nhất một trường cần lấy.');
                return;
            }

            startScrapeBtn.disabled = true;
            startScrapeBtn.textContent = 'Đang xử lý...';
            resultsPlaceholder.style.display = 'none';
            resultsOutput.style.display = 'none';
            loadingIndicator.style.display = 'flex';
            usageCard.style.display = 'none';

            try {
                console.log("Sending POST request to /api/web-scraper/start/"); // DEBUG
                const response = await fetch('/api/web-scraper/start/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({ url, fields, model })
                });
                
                const data = await response.json();
                console.log("Received response from server:", data); // DEBUG

                if (response.ok && data.status === 'ok') {
                    pollForStatus(data.task_id);
                } else {
                    alert('Lỗi: ' + (data.error || 'Không thể bắt đầu tác vụ.'));
                    resetUI();
                }

            } catch (error) {
                console.error('Lỗi khi bắt đầu scraping:', error);
                alert('Lỗi kết nối đến server.');
                resetUI();
            }
        });
    }

    function pollForStatus(taskId) {
        pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/web-scraper/status/${taskId}/`);
                const data = await response.json();

                if (data.status === 'COMPLETE') {
                    clearInterval(pollingInterval);
                    displayResults(data);
                    fetchHistory();
                } else if (data.status === 'FAILED') {
                    clearInterval(pollingInterval);
                    alert('Tác vụ trích xuất đã thất bại. Vui lòng kiểm tra log server.');
                    resetUI();
                }
            } catch (error) {
                clearInterval(pollingInterval);
                console.error('Lỗi khi kiểm tra trạng thái:', error);
                resetUI();
            }
        }, 5000);
    }

    function displayResults(taskData) {
        loadingIndicator.style.display = 'none';
        resultsOutput.style.display = 'flex';
        usageCard.style.display = 'block';

        inputTokensEl.textContent = taskData.input_tokens || 0;
        outputTokensEl.textContent = taskData.output_tokens || 0;
        totalCostEl.textContent = `$${parseFloat(taskData.cost || 0).toFixed(4)}`;

        downloadJsonBtn.onclick = () => window.location.href = `/download/scrape/${taskData.id}/json/`;
        downloadCsvBtn.onclick = () => window.location.href = `/download/scrape/${taskData.id}/csv/`;

        if(taskData.json_url) {
            fetch(taskData.json_url)
                .then(res => res.json())
                .then(jsonData => {
                    const tableHead = document.querySelector('#results-table thead');
                    const tableBody = document.querySelector('#results-table tbody');
                    tableHead.innerHTML = '';
                    tableBody.innerHTML = '';
                    
                    const dataKey = Object.keys(jsonData)[0];
                    const dataList = jsonData[dataKey];
                    
                    if(dataList && dataList.length > 0){
                        const headers = Object.keys(dataList[0]);
                        const headerRow = document.createElement('tr');
                        headers.forEach(header => {
                            const th = document.createElement('th');
                            th.textContent = header.replace(/_/g, ' ');
                            headerRow.appendChild(th);
                        });
                        tableHead.appendChild(headerRow);

                        dataList.forEach(item => {
                            const row = document.createElement('tr');
                            headers.forEach(header => {
                                const cell = document.createElement('td');
                                cell.textContent = item[header];
                                row.appendChild(cell);
                            });
                            tableBody.appendChild(row);
                        });
                    }
                });
        }
        resetUI(false);
    }
    
    function resetUI(clearResults = true) {
        startScrapeBtn.disabled = false;
        startScrapeBtn.textContent = 'Bắt đầu Trích xuất';
        loadingIndicator.style.display = 'none';
        if (clearResults) {
            resultsPlaceholder.style.display = 'flex';
            resultsOutput.style.display = 'none';
            usageCard.style.display = 'none';
        }
    }

    async function fetchHistory() {
        try {
            const response = await fetch('/api/web-scraper/history/');
            const data = await response.json();
            historyTableBody.innerHTML = '';

            if (data.history && data.history.length > 0) {
                data.history.forEach(item => {
                    const row = document.createElement('tr');
                    const isComplete = item.status === 'COMPLETE';
                    
                    row.innerHTML = `
                        <td>${item.created_at}</td>
                        <td title="${item.url}">${item.url.length > 40 ? item.url.substring(0, 40) + '...' : item.url}</td>
                        <td><span class="status-badge ${item.status.toLowerCase()}">${item.status}</span></td>
                        <td>
                            ${isComplete ? `
                                <a href="/download/scrape/${item.id}/json/" class="btn-secondary" style="font-size: 0.8rem; padding: 4px 8px;">JSON</a>
                                <a href="/download/scrape/${item.id}/csv/" class="btn-secondary" style="font-size: 0.8rem; padding: 4px 8px;">CSV</a>
                            ` : 'N/A'}
                        </td>
                    `;
                    historyTableBody.appendChild(row);
                });
            } else {
                historyTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #a0a0d0;">Chưa có lịch sử.</td></tr>';
            }
        } catch (error) {
            console.error('Lỗi khi lấy lịch sử:', error);
        }
    }

    deleteHistoryBtn.addEventListener('click', async () => {
        if (!confirm('Bạn có chắc chắn muốn xóa toàn bộ lịch sử không?')) {
            return;
        }
        try {
            await fetch('/api/web-scraper/history/delete/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            });
            fetchHistory();
        } catch (error) {
            console.error('Lỗi khi xóa lịch sử:', error);
        }
    });

    fetchHistory();
});