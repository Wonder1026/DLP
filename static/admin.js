// Загрузка списка ключевых слов при загрузке страницы
window.addEventListener('load', function() {
    loadKeywords();
    loadUsers();
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

        // Кнопка снятия прав (только для супер-админа)
        let actionButton = '';
        const userData = localStorage.getItem('user');
        if (userData) {
            const currentUserData = JSON.parse(userData);
            if (currentUserData.is_super_admin && user.is_admin && !user.is_super_admin) {
                actionButton = `<button onclick="removeAdmin(${user.id}, '${user.username}')" style="background: #dc3545; padding: 6px 12px; font-size: 12px;">Лишить статуса администратора</button>`;
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
}

function updateStats(users) {
    document.getElementById('userCount').textContent = users.length;

    const adminCount = users.filter(u => u.is_admin).length;
    document.getElementById('adminCount').textContent = adminCount;
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

