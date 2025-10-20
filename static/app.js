let ws = null;
let username = "Пользователь " + Math.floor(Math.random() * 1000);

// Подключаемся к WebSocket при загрузке страницы
window.addEventListener('load', function() {
    loadHistory();
    connectWebSocket();
});

async function loadHistory() {
    try {
        const response = await fetch('/api/messages/history?limit=20');
        const data = await response.json();

        console.log('📚 Загружена история:', data);

        data.messages.forEach(msg => {
            const messageType = msg.user === username ? 'sent' : 'received';
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
        console.log('📨 Получено сообщение:', data);

        // Определяем тип сообщения: своё или чужое
        const messageType = data.user === username ? 'sent' : 'received';
        addMessage(data.text, data.user, messageType, false);
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
        user: username,
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

// Отправка по Enter
document.getElementById('messageInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});