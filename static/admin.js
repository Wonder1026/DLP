// Загрузка списка ключевых слов при загрузке страницы
window.addEventListener('load', function() {
    loadStatistics();
    loadKeywords();
    loadUsers();
    loadViolations();
    loadFiles();
    loadUrls();
});

async function loadKeywords() {
    try {
        const response = await fetch('/api/dlp/keywords');
        const data = await response.json();

        displayKeywords(data.keywords);
        document.getElementById('keywordCount').textContent = data.count;

    } catch (error) {
        console.error('Ошибка загрузки ключевых слов:', error);
    }
}

function displayKeywords(keywords) {
    const container = document.getElementById('keywordList');
    container.innerHTML = '';

    if (keywords.length === 0) {
        container.innerHTML = '<div class="empty-state">Нет запрещённых слов</div>';
        return;
    }

    keywords.forEach(keyword => {
        const tag = document.createElement('div');
        tag.className = 'keyword-tag';
        tag.innerHTML = `
            <span>${keyword}</span>
            <button onclick="removeKeyword('${keyword}')" title="Удалить">✕</button>
        `;
        container.appendChild(tag);
    });

    // Обновляем счётчик
    document.getElementById('keywordCount').textContent = keywords.length;
}

async function addKeyword() {
    const input = document.getElementById('newKeyword');
    const keyword = input.value.trim();

    if (!keyword) {
        alert('Введите ключевое слово!');
        return;
    }

    try {
        const response = await fetch('/api/dlp/keywords', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ keyword: keyword })
        });

        const data = await response.json();

        if (data.status === 'success') {
            displayKeywords(data.keywords);
            document.getElementById('keywordCount').textContent = data.keywords.length;
            input.value = '';
        }

    } catch (error) {
        console.error('Ошибка добавления:', error);
        alert('❌ Ошибка при добавлении');
    }
}

async function removeKeyword(keyword) {
    if (!confirm(`Удалить слово "${keyword}"?`)) {
        return;
    }

    try {
        const response = await fetch('/api/dlp/keywords', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ keyword: keyword })
        });

        const data = await response.json();

        if (data.status === 'success') {
            displayKeywords(data.keywords);
            document.getElementById('keywordCount').textContent = data.keywords.length;
        }

    } catch (error) {
        console.error('Ошибка удаления:', error);
        alert('❌ Ошибка при удалении');
    }
}

async function testMessage() {
    const input = document.getElementById('testMessage');
    const text = input.value.trim();

    if (!text) {
        alert('Введите текст для проверки!');
        return;
    }

    try {
        const response = await fetch('/api/dlp/keywords/test?text=' + encodeURIComponent(text), {
            method: 'POST'
        });

        const data = await response.json();

        const resultDiv = document.getElementById('testResult');
        const className = data.allowed ? 'allowed' : 'blocked';

        let foundKeywords = '';
        if (data.found_keywords && data.found_keywords.length > 0) {
            foundKeywords = `<br><strong>Найдены слова:</strong> ${data.found_keywords.join(', ')}`;
        }

        resultDiv.className = `test-result ${className}`;
        resultDiv.innerHTML = `
            <strong>${data.allowed ? '✅ Разрешено' : '❌ Заблокировано'}</strong><br>
            ${data.reason}
            ${foundKeywords}
        `;

    } catch (error) {
        console.error('Ошибка тестирования:', error);
    }
}

// Загрузка списка пользователей
async function loadUsers() {
    try {
        const userData = localStorage.getItem('user');
        if (!userData) return;

        const user = JSON.parse(userData);

        const response = await fetch(`/api/auth/users?admin_id=${user.id}`);
        const data = await response.json();

        displayUsers(data.users);
        updateStats(data.users);

    } catch (error) {
        console.error('Ошибка загрузки пользователей:', error);
    }
}

function displayUsers(users) {
    const container = document.getElementById('usersList');
    container.innerHTML = '';

    if (users.length === 0) {
        container.innerHTML = '<div class="empty-state">Нет пользователей</div>';
        return;
    }

    const table = document.createElement('div');
    table.className = 'users-table';

    users.forEach(user => {
        const row = document.createElement('div');
        row.className = 'user-row';

        const initial = user.display_name.charAt(0).toUpperCase();

        let badges = '';
        if (user.is_super_admin) {
            badges = '<span class="admin-badge" style="background: #dc3545;">SUPER ADMIN</span>';
        } else if (user.is_admin) {
            badges = '<span class="admin-badge">ADMIN</span>';
        }

        if (user.is_banned) {
            badges += '<span class="admin-badge" style="background: #6c757d;">BANNED</span>';
        }

        if (user.violation_count > 0) {
            const violationColor = user.violation_count >= 7 ? '#dc3545' : user.violation_count >= 4 ? '#ffc107' : '#17a2b8';
            badges += `<span class="admin-badge" style="background: ${violationColor};">⚠️ ${user.violation_count} нарушений</span>`;
        }

        // Кнопка снятия прав (только для супер-админа)
        // Кнопки действий
        let actionButton = '';
        const userData = localStorage.getItem('user');
        if (userData) {
            const currentUserData = JSON.parse(userData);

            // Если пользователь забанен
            if (user.is_banned) {
                if (currentUserData.is_admin) {
                    actionButton = `
                <button onclick="unbanUser(${user.id}, '${user.username}')" style="background: #28a745; padding: 6px 12px; font-size: 12px; margin-right: 5px;">Разбанить</button>
                <button onclick="resetViolations(${user.id}, '${user.username}')" style="background: #17a2b8; padding: 6px 12px; font-size: 12px;">Сбросить нарушения</button>
            `;
                }
            }
            // Если есть нарушения, но не забанен
            else if (user.violation_count > 0) {
                if (currentUserData.is_admin && !user.is_admin) {
                    // Админ может забанить пользователя с нарушениями
                    actionButton = `
                <button onclick="banUser(${user.id}, '${user.username}')" style="background: #dc3545; padding: 6px 12px; font-size: 12px; margin-right: 5px;">Забанить</button>
                <button onclick="resetViolations(${user.id}, '${user.username}')" style="background: #17a2b8; padding: 6px 12px; font-size: 12px;">Сбросить нарушения (${user.violation_count})</button>
            `;
                } else if (currentUserData.is_admin) {
                    actionButton = `<button onclick="resetViolations(${user.id}, '${user.username}')" style="background: #17a2b8; padding: 6px 12px; font-size: 12px;">Сбросить нарушения (${user.violation_count})</button>`;
                }
            }
            // Если это обычный пользователь без нарушений
            else if (currentUserData.is_admin && !user.is_admin && !user.is_super_admin) {
                actionButton = `<button onclick="banUser(${user.id}, '${user.username}')" style="background: #dc3545; padding: 6px 12px; font-size: 12px;">Забанить</button>`;
            }
            // Кнопка снятия админки (только для супер-админа)
            if (currentUserData.is_super_admin && user.is_admin && !user.is_super_admin) {
                if (actionButton) {
                    actionButton += ' ';
                }
                actionButton += `<button onclick="removeAdmin(${user.id}, '${user.username}')" style="background: #6c757d; padding: 6px 12px; font-size: 12px;">Снять админа</button>`;
            }
        }

        row.innerHTML = `
            <div class="user-info">
                <div class="user-avatar">${initial}</div>
                <div class="user-details">
                    <div>
                        <strong>${user.display_name}</strong>
                        ${badges}
                    </div>
                    <div class="username">@${user.username}</div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 15px;">
                <div class="user-id">ID: ${user.id}</div>
                ${actionButton}
            </div>
        `;

        table.appendChild(row);
    });

    container.appendChild(table);
    updateStats(users);
}

function updateStats(users) {
    // Обновляем только счётчики пользователей
    document.getElementById('userCount').textContent = users.length;

    const adminCount = users.filter(u => u.is_admin).length;
    document.getElementById('adminCount').textContent = adminCount;

    const bannedCount = users.filter(u => u.is_banned).length;
    document.getElementById('bannedUsersCount').textContent = bannedCount;
}

async function makeAdmin() {
    const input = document.getElementById('makeAdminUsername');
    const username = input.value.trim();

    if (!username) {
        alert('Введите username!');
        return;
    }

    const userData = localStorage.getItem('user');
    if (!userData) {
        alert('Ошибка: не авторизован');
        return;
    }

    const user = JSON.parse(userData);

    try {
        const response = await fetch(`/api/auth/make-admin?admin_id=${user.id}&target_username=${encodeURIComponent(username)}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            alert(`✅ ${data.message}`);
            input.value = '';
            loadUsers(); // Перезагружаем список
        } else {
            alert(`❌ ${data.detail}`);
        }

    } catch (error) {
        console.error('Ошибка:', error);
        alert('❌ Ошибка при назначении администратора');
    }
}

// Отправка по Enter в полях ввода
document.getElementById('newKeyword').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') addKeyword();
});

document.getElementById('testMessage').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') testMessage();
});

document.getElementById('makeAdminUsername').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') makeAdmin();
});

async function removeAdmin(userId, username) {
    if (!confirm(`Снять права администратора у "${username}"?`)) {
        return;
    }

    const userData = localStorage.getItem('user');
    if (!userData) {
        alert('Ошибка: не авторизован');
        return;
    }

    const user = JSON.parse(userData);

    if (!user.is_super_admin) {
        alert('❌ Доступ запрещён! Только для главного администратора.');
        return;
    }

    try {
        const response = await fetch(`/api/auth/remove-admin?super_admin_id=${user.id}&target_user_id=${userId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            alert(`✅ ${data.message}`);
            loadUsers(); // Перезагружаем список
        } else {
            alert(`❌ ${data.detail}`);
        }

    } catch (error) {
        console.error('Ошибка:', error);
        alert('❌ Ошибка при снятии прав');
    }
}

// Загрузка нарушений
async function loadViolations() {
    try {
        const userData = localStorage.getItem('user');
        if (!userData) return;

        const user = JSON.parse(userData);
        const showOnlyUnreviewed = document.getElementById('showOnlyUnreviewed').checked;

        let url = `/api/violations/?admin_id=${user.id}`;
        if (showOnlyUnreviewed) {
            url += '&is_reviewed=false';
        }

        const response = await fetch(url);
        const data = await response.json();

        displayViolations(data.violations);
        updateViolationsStats(data.violations);

    } catch (error) {
        console.error('Ошибка загрузки нарушений:', error);
    }
}

function displayViolations(violations) {
    const container = document.getElementById('violationsList');
    container.innerHTML = '';

    if (violations.length === 0) {
        container.innerHTML = '<div class="empty-state">Нет нарушений</div>';
        return;
    }

    violations.forEach(violation => {
        const card = document.createElement('div');
        card.className = `violation-card ${violation.is_reviewed ? 'reviewed' : ''}`;

        const initial = violation.display_name.charAt(0).toUpperCase();
        const reviewedBadge = violation.is_reviewed
            ? '<span class="reviewed-badge">✓ Проверено</span>'
            : '';

        const keywordsBadges = violation.found_keywords
            .map(kw => `<span class="keyword-badge">${kw}</span>`)
            .join('');

        const actions = violation.is_reviewed
            ? ''
            : `
                <div class="violation-actions">
                    <button class="btn-ban" onclick="banUserFromViolation(${violation.user_id}, '${violation.username}', ${violation.id})">
                        🚫 Забанить пользователя
                    </button>
                    <button class="btn-review" onclick="markViolationAsReviewed(${violation.id})">
                        ✓ Отметить проверенным
                    </button>
                </div>
            `;

        card.innerHTML = `
            <div class="violation-header">
                <div class="violation-user">
                    <div class="violation-avatar">${initial}</div>
                    <div>
                        <strong>${violation.display_name}</strong>
                        <div style="font-size: 12px; color: #999;">@${violation.username} (ID: ${violation.user_id})</div>
                    </div>
                </div>
                <div style="text-align: right;">
                    ${reviewedBadge}
                    <div class="violation-date">${violation.created_at}</div>
                </div>
            </div>
            
            <div class="violation-message">
                <strong>Заблокированное сообщение:</strong><br>
                "${violation.message_text}"
            </div>
            
            <div class="violation-keywords">
                <strong>Найденные запрещённые слова:</strong><br>
                ${keywordsBadges}
            </div>
            
            ${actions}
        `;

        container.appendChild(card);
    });
}

function updateViolationsStats(violations) {
    document.getElementById('violationsCount').textContent = violations.length;

    const unreviewedCount = violations.filter(v => !v.is_reviewed).length;
    document.getElementById('unreviewedCount').textContent = unreviewedCount;

    // Обновляем общую статистику
    // loadStatistics();
}

async function banUserFromViolation(userId, username, violationId) {
    if (!confirm(`Забанить пользователя "${username}"?\n\nПользователь не сможет отправлять сообщения в чат.`)) {
        return;
    }

    const userData = localStorage.getItem('user');
    if (!userData) return;

    const user = JSON.parse(userData);

    try {
        const response = await fetch(`/api/auth/ban-user?admin_id=${user.id}&target_user_id=${userId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            alert(`✅ ${data.message}`);

            // Автоматически отмечаем нарушение как проверенное
            await markViolationAsReviewed(violationId, false);

            loadViolations();
            loadUsers();
        } else {
            alert(`❌ ${data.detail}`);
        }

    } catch (error) {
        console.error('Ошибка:', error);
        alert('❌ Ошибка при бане пользователя');
    }
}

async function markViolationAsReviewed(violationId, showAlert = true) {
    const userData = localStorage.getItem('user');
    if (!userData) return;

    const user = JSON.parse(userData);

    try {
        const response = await fetch(`/api/violations/${violationId}/review?admin_id=${user.id}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            if (showAlert) {
                alert('✅ Нарушение отмечено как проверенное');
            }
            loadViolations();
        } else {
            if (showAlert) {
                alert('❌ Ошибка');
            }
        }

    } catch (error) {
        console.error('Ошибка:', error);
    }
}


async function unbanUser(userId, username) {
    if (!confirm(`Разбанить пользователя "${username}"?`)) {
        return;
    }

    const userData = localStorage.getItem('user');
    if (!userData) return;

    const user = JSON.parse(userData);

    try {
        const response = await fetch(`/api/auth/unban-user?admin_id=${user.id}&target_user_id=${userId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            alert(`✅ ${data.message}`);
            loadUsers();
        } else {
            alert(`❌ ${data.detail}`);
        }

    } catch (error) {
        console.error('Ошибка:', error);
        alert('❌ Ошибка при разбане пользователя');
    }
}

// Загрузка файлов
async function loadFiles() {
    try {
        const userData = localStorage.getItem('user');
        if (!userData) return;

        const user = JSON.parse(userData);
        const showOnlyPending = document.getElementById('showOnlyPendingFiles').checked;

        let url = showOnlyPending
            ? `/api/files/pending?admin_id=${user.id}`
            : `/api/files/all?admin_id=${user.id}`;

        const response = await fetch(url);
        const data = await response.json();

        displayFiles(data.files);
        updateFilesStats(data.files);

    } catch (error) {
        console.error('Ошибка загрузки файлов:', error);
    }
}

function displayFiles(files) {
    const container = document.getElementById('filesList');
    container.innerHTML = '';

    if (files.length === 0) {
        container.innerHTML = '<div class="empty-state">Нет файлов</div>';
        return;
    }

    files.forEach(file => {
        const card = document.createElement('div');
        card.className = `file-card ${file.status}`;

        const fileIcon = getFileIconForAdmin(file.filename);
        const fileSize = formatFileSize(file.file_size);

        // Бейдж типа модерации
        const moderationBadge = file.moderation_type === 'virustotal'
            ? '<span style="background: #17a2b8; color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px; margin-left: 8px;">🌐 VirusTotal</span>'
            : '<span style="background: #6c757d; color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px; margin-left: 8px;">🛡️ Ручная</span>';

        const statusBadge = file.status === 'pending'
            ? '<span class="file-status-badge pending">⏳ На модерации</span>'
            : file.status === 'approved'
            ? '<span class="file-status-badge approved">✓ Одобрено</span>'
            : '<span class="file-status-badge rejected">✗ Отклонено</span>';

        // Кнопки действий в зависимости от типа модерации
        let actions = '';
        if (file.status === 'pending') {
            if (file.moderation_type === 'virustotal') {
                actions = `
                    <div class="file-actions">
                        <button class="btn-approve" style="background: #17a2b8;" onclick="checkVirusTotal(${file.id})">
                            🔍 Проверить VirusTotal
                        </button>
                        <button class="btn-approve" onclick="approveFile(${file.id})">
                            ✓ Одобрить вручную
                        </button>
                        <button class="btn-reject" onclick="rejectFile(${file.id})">
                            ✗ Отклонить
                        </button>
                    </div>
                `;
            } else {
                actions = `
                    <div class="file-actions">
                        <button class="btn-approve" onclick="approveFile(${file.id})">
                            ✓ Одобрить
                        </button>
                        <button class="btn-reject" onclick="rejectFile(${file.id})">
                            ✗ Отклонить
                        </button>
                    </div>
                `;
            }
        }

        // Результат VirusTotal (если есть)
        let virusTotalResult = '';
        if (file.virustotal_result) {
            try {
                const result = JSON.parse(file.virustotal_result);
                virusTotalResult = `
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 6px; margin-top: 10px; font-size: 13px;">
                        <strong>Результат VirusTotal:</strong><br>
                        ${result.summary || 'Проверка завершена'}
                    </div>
                `;
            } catch (e) {
                console.error('Ошибка парсинга результата VirusTotal:', e);
            }
        }

        card.innerHTML = `
            <div class="file-header">
                <div class="file-user">
                    <div class="file-icon-big">${fileIcon}</div>
                    <div>
                        <strong>${file.display_name}</strong>
                        <div style="font-size: 12px; color: #999;">@${file.username} (ID: ${file.user_id})</div>
                    </div>
                </div>
                <div style="text-align: right;">
                    ${statusBadge}
                    ${moderationBadge}
                    <div style="font-size: 12px; color: #999; margin-top: 4px;">${file.created_at}</div>
                </div>
            </div>
            
            <div class="file-details">
                <div class="file-filename">📄 ${file.filename}</div>
                <div class="file-meta">
                    <strong>Размер:</strong> ${fileSize} | 
                    <strong>Тип:</strong> ${file.file_type.toUpperCase()}
                </div>
            </div>
            
            ${virusTotalResult}
            ${actions}
        `;

        container.appendChild(card);
    });
}

function updateFilesStats(files) {
    document.getElementById('filesCount').textContent = files.length;

    const pendingCount = files.filter(f => f.status === 'pending').length;
    document.getElementById('pendingFilesCount').textContent = pendingCount;
}

function getFileIconForAdmin(filename) {
    const ext = filename.substring(filename.lastIndexOf('.')).toLowerCase();

    switch(ext) {
        case '.exe':
            return '⚙️';
        case '.doc':
        case '.docx':
            return '📄';
        default:
            return '📎';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

async function approveFile(fileId) {
    if (!confirm('Одобрить этот файл?')) {
        return;
    }

    const userData = localStorage.getItem('user');
    if (!userData) return;

    const user = JSON.parse(userData);

    try {
        const response = await fetch(`/api/files/${fileId}/approve?admin_id=${user.id}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            alert(`✅ ${data.message}`);
            loadFiles();
        } else {
            alert(`❌ ${data.detail}`);
        }

    } catch (error) {
        console.error('Ошибка:', error);
        alert('❌ Ошибка при одобрении файла');
    }
}

async function rejectFile(fileId) {
    if (!confirm('Отклонить этот файл?')) {
        return;
    }

    const userData = localStorage.getItem('user');
    if (!userData) return;

    const user = JSON.parse(userData);

    try {
        const response = await fetch(`/api/files/${fileId}/reject?admin_id=${user.id}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            alert(`✅ ${data.message}`);
            loadFiles();
        } else {
            alert(`❌ ${data.detail}`);
        }

    } catch (error) {
        console.error('Ошибка:', error);
        alert('❌ Ошибка при отклонении файла');
    }
}

async function checkVirusTotal(fileId) {
    if (!confirm('Проверить файл через VirusTotal API?\n\nФайл будет отправлен на внешний сервис для анализа.')) {
        return;
    }

    const userData = localStorage.getItem('user');
    if (!userData) return;

    const user = JSON.parse(userData);

    // Показываем индикатор загрузки
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '⏳ Проверка...';
    button.disabled = true;

    try {
        const response = await fetch(`/api/files/${fileId}/check-virustotal?admin_id=${user.id}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            const result = data.virustotal_result;
            alert(`🔍 Результат VirusTotal:\n\n${result.summary}`);
            loadFiles();
        } else {
            alert(`❌ ${data.detail}`);
            button.innerHTML = originalText;
            button.disabled = false;
        }

    } catch (error) {
        console.error('Ошибка:', error);
        alert('❌ Ошибка при проверке файла');
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

let violationsChart = null;
let filesChart = null;
let urlsChart = null;

async function loadStatistics() {
    try {
        const userData = localStorage.getItem('user');
        if (!userData) return;

        const user = JSON.parse(userData);

        const response = await fetch(`/api/violations/statistics?admin_id=${user.id}`);
        const data = await response.json();

        // Основные метрики
        document.getElementById('totalMessagesCount').textContent = data.total_messages;
        document.getElementById('blockedMessagesCount').textContent = data.total_violations;
        document.getElementById('sensitiveDataCount').textContent = data.sensitive_data_violations;
        document.getElementById('blockRatePercent').textContent = data.block_rate + '%';

        // График нарушений за неделю
        renderViolationsChart(data.violations_by_day);

        // График файлов
        renderFilesChart(data.files);

        // График URL
        renderUrlsChart(data.urls);

        // Топ нарушителей
        renderTopViolators(data.top_violators);

    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
    }
}

function renderViolationsChart(violationsByDay) {
    const ctx = document.getElementById('violationsChart');

    // Уничтожаем старый график если есть
    if (violationsChart) {
        violationsChart.destroy();
    }

    const labels = Object.keys(violationsByDay);
    const data = Object.values(violationsByDay);

    violationsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Нарушений',
                data: data,
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function renderFilesChart(filesData) {
    const ctx = document.getElementById('filesChart');

    if (filesChart) {
        filesChart.destroy();
    }

    filesChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Одобрено', 'На модерации', 'Отклонено'],
            datasets: [{
                data: [filesData.approved, filesData.pending, filesData.rejected],
                backgroundColor: ['#28a745', '#ffc107', '#dc3545']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function renderUrlsChart(urlsData) {
    const ctx = document.getElementById('urlsChart');

    if (urlsChart) {
        urlsChart.destroy();
    }

    urlsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Безопасные', 'Опасные'],
            datasets: [{
                label: 'Количество',
                data: [urlsData.safe, urlsData.malicious],
                backgroundColor: ['#28a745', '#dc3545']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function renderTopViolators(violators) {
    const container = document.getElementById('topViolatorsList');
    container.innerHTML = '';

    if (violators.length === 0) {
        container.innerHTML = '<p style="color: #999; text-align: center;">Нет нарушителей</p>';
        return;
    }

    violators.forEach((violator, index) => {
        const row = document.createElement('div');
        row.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            margin-bottom: 8px;
            background: ${index % 2 === 0 ? '#f8f9fa' : 'white'};
            border-radius: 6px;
            border-left: 4px solid ${violator.is_banned ? '#dc3545' : '#ffc107'};
        `;

        const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`;
        const bannedBadge = violator.is_banned ? '<span style="background: #dc3545; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; margin-left: 8px;">BANNED</span>' : '';

        row.innerHTML = `
            <div>
                <span style="font-size: 20px; margin-right: 10px;">${medal}</span>
                <strong>${violator.display_name}</strong>
                <span style="color: #999; font-size: 13px;">@${violator.username}</span>
                ${bannedBadge}
            </div>
            <div style="font-size: 18px; font-weight: bold; color: ${violator.is_banned ? '#dc3545' : '#ffc107'};">
                ${violator.violation_count} нарушений
            </div>
        `;

        container.appendChild(row);
    });
}

async function resetViolations(userId, username) {
    if (!confirm(`Сбросить счётчик нарушений у "${username}"?`)) {
        return;
    }

    const userData = localStorage.getItem('user');
    if (!userData) return;

    const user = JSON.parse(userData);

    try {
        const response = await fetch(`/api/auth/reset-violations?admin_id=${user.id}&target_user_id=${userId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            alert(`✅ ${data.message}`);
            loadUsers();
        } else {
            alert(`❌ ${data.detail}`);
        }

    } catch (error) {
        console.error('Ошибка:', error);
        alert('❌ Ошибка при сбросе нарушений');
    }
}

// Загрузка URL проверок
async function loadUrls() {
    try {
        const userData = localStorage.getItem('user');
        if (!userData) return;

        const user = JSON.parse(userData);
        const showOnlyPending = document.getElementById('showOnlyPendingUrls').checked;

        let url = showOnlyPending
            ? `/api/url-checks/pending?admin_id=${user.id}`
            : `/api/url-checks/all?admin_id=${user.id}`;

        const response = await fetch(url);
        const data = await response.json();

        displayUrls(data.urls);
        updateUrlsStats(data.urls);

    } catch (error) {
        console.error('Ошибка загрузки URL:', error);
    }
}

function displayUrls(urls) {
    const container = document.getElementById('urlsList');
    container.innerHTML = '';

    if (urls.length === 0) {
        container.innerHTML = '<div class="empty-state">Нет ссылок на проверке</div>';
        return;
    }

    urls.forEach(urlCheck => {
        const card = document.createElement('div');
        card.className = `url-card ${urlCheck.status}`;

        const initial = urlCheck.display_name.charAt(0).toUpperCase();

        const statusBadge = urlCheck.status === 'pending'
            ? '<span class="url-status-badge pending">⏳ На проверке</span>'
            : urlCheck.status === 'safe'
                ? '<span class="url-status-badge safe">✅ Безопасно</span>'
                : urlCheck.status === 'malicious'
                    ? '<span class="url-status-badge malicious">⚠️ Опасно</span>'
                    : '<span class="url-status-badge suspicious">⚠️ Подозрительно</span>';

        // Кнопки действий
        let actions = '';
        if (urlCheck.status === 'pending') {
            actions = `
                <div class="file-actions">
                    <button style="background: #17a2b8;" onclick="scanUrlVirusTotal(${urlCheck.id})">
                        🔍 Проверить VirusTotal
                    </button>
                    <button class="btn-approve" onclick="markUrlSafe(${urlCheck.id})">
                        ✅ Безопасно
                    </button>
                    <button class="btn-reject" onclick="markUrlMalicious(${urlCheck.id})">
                        ⚠️ Опасно
                    </button>
                </div>
            `;
        }

        // Результат VirusTotal
        let virusTotalResult = '';
        if (urlCheck.virustotal_result) {
            try {
                const result = JSON.parse(urlCheck.virustotal_result);
                virusTotalResult = `
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 6px; margin-top: 10px; font-size: 13px;">
                        <strong>Результат VirusTotal:</strong><br>
                        ${result.summary || 'Проверка завершена'}
                    </div>
                `;
            } catch (e) {
                console.error('Ошибка парсинга результата:', e);
            }
        }

        card.innerHTML = `
            <div class="file-header">
                <div class="file-user">
                    <div class="violation-avatar">${initial}</div>
                    <div>
                        <strong>${urlCheck.display_name}</strong>
                        <div style="font-size: 12px; color: #999;">@${urlCheck.username} (ID: ${urlCheck.user_id})</div>
                    </div>
                </div>
                <div style="text-align: right;">
                    ${statusBadge}
                    <div style="font-size: 12px; color: #999; margin-top: 4px;">${urlCheck.created_at}</div>
                </div>
            </div>
            
            <div style="margin: 10px 0;">
                <strong>Сообщение:</strong><br>
                <div style="background: #f8f9fa; padding: 10px; border-radius: 6px; margin-top: 5px;">
                    ${urlCheck.message_text}
                </div>
            </div>
            
            <div style="margin: 10px 0;">
                <strong>Ссылка:</strong><br>
                <div class="url-link">
                    <a href="${urlCheck.url}" target="_blank" style="color: #17a2b8; text-decoration: none;">
                        ${urlCheck.url} 🔗
                    </a>
                </div>
            </div>
            
            ${virusTotalResult}
            ${actions}
        `;

        container.appendChild(card);
    });
}

function updateUrlsStats(urls) {
    document.getElementById('urlsCount').textContent = urls.length;

    const pendingCount = urls.filter(u => u.status === 'pending').length;
    document.getElementById('pendingUrlsCount').textContent = pendingCount;

    const maliciousCount = urls.filter(u => u.status === 'malicious').length;
    document.getElementById('maliciousUrlsCount').textContent = maliciousCount;
}

async function scanUrlVirusTotal(urlCheckId) {
    if (!confirm('Проверить ссылку через VirusTotal API?')) {
        return;
    }

    const userData = localStorage.getItem('user');
    if (!userData) return;

    const user = JSON.parse(userData);

    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '⏳ Проверка...';
    button.disabled = true;

    try {
        const response = await fetch(`/api/url-checks/${urlCheckId}/scan?admin_id=${user.id}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            const result = data.virustotal_result;
            alert(`🔍 Результат VirusTotal:\n\n${result.summary}`);
            loadUrls();
        } else {
            alert(`❌ ${data.detail}`);
            button.innerHTML = originalText;
            button.disabled = false;
        }

    } catch (error) {
        console.error('Ошибка:', error);
        alert('❌ Ошибка при проверке URL');
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

async function markUrlSafe(urlCheckId) {
    if (!confirm('Отметить ссылку как безопасную?')) {
        return;
    }

    const userData = localStorage.getItem('user');
    if (!userData) return;

    const user = JSON.parse(userData);

    try {
        const response = await fetch(`/api/url-checks/${urlCheckId}/mark-safe?admin_id=${user.id}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            alert(`✅ ${data.message}`);
            loadUrls();
        } else {
            alert(`❌ ${data.detail}`);
        }

    } catch (error) {
        console.error('Ошибка:', error);
        alert('❌ Ошибка при обновлении статуса');
    }
}

async function markUrlMalicious(urlCheckId) {
    if (!confirm('Отметить ссылку как ОПАСНУЮ?')) {
        return;
    }

    const userData = localStorage.getItem('user');
    if (!userData) return;

    const user = JSON.parse(userData);

    try {
        const response = await fetch(`/api/url-checks/${urlCheckId}/mark-malicious?admin_id=${user.id}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            alert(`⚠️ ${data.message}`);
            loadUrls();
        } else {
            alert(`❌ ${data.detail}`);
        }

    } catch (error) {
        console.error('Ошибка:', error);
        alert('❌ Ошибка при обновлении статуса');
    }
}

async function banUser(userId, username) {
    if (!confirm(`Забанить пользователя "${username}"?\n\nПользователь не сможет отправлять сообщения.`)) {
        return;
    }

    const userData = localStorage.getItem('user');
    if (!userData) return;

    const user = JSON.parse(userData);

    try {
        const response = await fetch(`/api/auth/ban-user?admin_id=${user.id}&target_user_id=${userId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            alert(`✅ ${data.message}`);
            loadUsers();
            loadStatistics();
        } else {
            alert(`❌ ${data.detail}`);
        }

    } catch (error) {
        console.error('Ошибка:', error);
        alert('❌ Ошибка при бане пользователя');
    }
}