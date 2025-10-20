let ws = null;
let currentUser = null;

// Проверка авторизации при загрузке страницы
window.addEventListener('load', function() {
    // Проверяем, есть ли данные пользователя
    const userData = localStorage.getItem('user');

    if (!userData) {
        // Пользователь не авторизован - редирект на страницу входа
        window.location.href = '/login';
        return;
    }

    // Парсим данные пользователя
    currentUser = JSON.parse(userData);
    console.log('Текущий пользователь:', currentUser);

    // Отображаем имя пользователя
    displayUserInfo();

    // Загружаем историю и подключаемся к WebSocket
    loadHistory();
    connectWebSocket();
});

// function displayUserInfo() {
//     // Покажем имя пользователя в интерфейсе (добавим позже)
//     console.log('Вошёл как:', currentUser.display_name);
// }

async function loadHistory() {
    try {
        const response = await fetch('/api/messages/history?limit=20');
        const data = await response.json();

        console.log('📚 Загружена история:', data);

        data.messages.forEach(msg => {
            const messageType = msg.user === currentUser.display_name ? 'sent' : 'received';
            addMessage(msg.text, msg.user, messageType, true);
        });

    } catch (error) {
        console.error('Ошибка загрузки истории:', error);
    }
}

function connectWebSocket() {
    ws = new WebSocket('ws://localhost:8000/ws');

    ws.onopen = function() {
        console.log('✅ WebSocket подключен');
        addSystemMessage('Подключено к серверу');
    };

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('📨 Получено:', data);

    // Обработка ошибки (блокировка DLP)
    if (data.type === 'error') {
        addSystemMessage(data.message);
        return;
    }

    // Обычное сообщение
    if (data.type === 'message') {
        const messageType = data.user === currentUser.display_name ? 'sent' : 'received';
        addMessage(data.text, data.user, messageType, false);
    }
};

    ws.onerror = function(error) {
        console.error('❌ Ошибка WebSocket:', error);
        addSystemMessage('Ошибка подключения');
    };

    ws.onclose = function() {
        console.log('🔌 WebSocket отключен');
        addSystemMessage('Отключено от сервера');
    };
}

function sendMessage() {
    const input = document.getElementById('messageInput');
    const text = input.value.trim();

    if (!text || !ws) return;

    // Отправляем через WebSocket
    const message = {
        user_id: currentUser.id,           // ← добавили
        username: currentUser.username,     // ← добавили
        user: currentUser.display_name,
        text: text,
        timestamp: new Date().toLocaleTimeString()
    };

    ws.send(JSON.stringify(message));

    input.value = '';
}

function addMessage(text, user, type, isHistory = false) {
    const chatBox = document.getElementById('chatBox');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    const displayName = type === 'sent' ? 'Вы' : user;
    messageDiv.innerHTML = `<strong>${displayName}:</strong> ${text}`;

    chatBox.appendChild(messageDiv);

    // Прокручиваем вниз только для новых сообщений
    if (!isHistory) {
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

function addSystemMessage(text) {
    const chatBox = document.getElementById('chatBox');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';
    messageDiv.innerHTML = `<em>Система: ${text}</em>`;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function logout() {
    if (confirm('Выйти из аккаунта?')) {
        localStorage.removeItem('user');
        window.location.href = '/login';
    }
}

// Обновляем отображение информации о пользователе
function displayUserInfo() {
    const userInfoElement = document.getElementById('userInfo');
    if (userInfoElement) {
        userInfoElement.textContent = `👤 ${currentUser.display_name} (${currentUser.username})`;
    }

    // Показываем ссылку на админку только администраторам
    const adminLink = document.getElementById('adminLink');
    if (adminLink) {
        if (currentUser.is_admin) {
            adminLink.style.display = 'inline';
        } else {
            adminLink.style.display = 'none';
        }
    }
}

// Отправка по Enter
document.getElementById('messageInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});