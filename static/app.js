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
        // Загружаем текстовые сообщения
        const messagesResponse = await fetch('/api/messages/history?limit=50');
        const messagesData = await messagesResponse.json();

        console.log('📚 Загружена история сообщений:', messagesData);

        messagesData.messages.forEach(msg => {
            const messageType = msg.user === currentUser.display_name ? 'sent' : 'received';
            addMessage(msg.text, msg.user, messageType, true);
        });

        // Загружаем одобренные файлы всех пользователей
        const approvedFilesResponse = await fetch('/api/files/approved');
        const approvedFilesData = await approvedFilesResponse.json();

        console.log('📎 Загружены одобренные файлы:', approvedFilesData);

        approvedFilesData.files.forEach(file => {
            const messageType = file.user_id === currentUser.id ? 'sent' : 'received';
            addFileMessage(file, messageType);
        });

        // Загружаем свои файлы (включая pending и rejected)
        const myFilesResponse = await fetch(`/api/files/my-files?user_id=${currentUser.id}`);
        const myFilesData = await myFilesResponse.json();

        console.log('📎 Загружены мои файлы:', myFilesData);

        myFilesData.files.forEach(file => {
            // Показываем только те, которых ещё нет (pending и rejected)
            if (file.status !== 'approved') {
                addFileMessage(file, 'sent');
            }
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

    // Обновление статуса файла
    if (data.type === 'file_status_update') {
        updateFileStatus(data.file_id, data.status);
        return;
    }

    // Файл
    if (data.type === 'file') {
        // Не добавляем файл дважды себе
        if (data.user_id !== currentUser.id) {
            addFileMessage(data.file, 'received');
        }
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


async function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Проверка расширения
    const allowedExtensions = ['.exe', '.doc', '.docx'];
    const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

    if (!allowedExtensions.includes(fileExt)) {
        alert('❌ Недопустимый тип файла.\nРазрешены: .exe, .doc, .docx');
        event.target.value = '';
        return;
    }

    // Проверка размера (50 MB)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
        alert('❌ Файл слишком большой.\nМаксимальный размер: 50 MB');
        event.target.value = '';
        return;
    }

    // Показываем сообщение о загрузке
    addFileUploadingMessage(file);

    // Загружаем файл
    await uploadFile(file);

    // Очищаем input
    event.target.value = '';
}

function addFileUploadingMessage(file) {
    const chatBox = document.getElementById('chatBox');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'file-message sent';
    messageDiv.id = 'uploading-file';

    const fileIcon = getFileIcon(file.name);
    const fileSize = formatFileSize(file.size);

    messageDiv.innerHTML = `
        <div class="file-icon">${fileIcon}</div>
        <div class="file-name">${file.name}</div>
        <div class="file-size">${fileSize}</div>
        <div class="file-status pending">⏳ Загрузка...</div>
        <div class="upload-progress">
            <div class="upload-progress-bar" style="width: 0%"></div>
        </div>
    `;

    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        // Имитация прогресса
        const progressBar = document.querySelector('#uploading-file .upload-progress-bar');
        if (progressBar) {
            progressBar.style.width = '50%';
        }

        const response = await fetch(`/api/files/upload?user_id=${currentUser.id}`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (progressBar) {
            progressBar.style.width = '100%';
        }

        // Удаляем сообщение о загрузке
        const uploadingMsg = document.getElementById('uploading-file');
        if (uploadingMsg) {
            uploadingMsg.remove();
        }

        if (response.ok) {
            // Добавляем сообщение об успешной загрузке себе
            addFileMessage(data.file, 'sent');

            // Отправляем уведомление ВСЕМ через WebSocket
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'file',
                    user_id: currentUser.id,
                    username: currentUser.username,
                    user: currentUser.display_name,
                    file: data.file  // Отправляем полную информацию о файле
                }));
            }
        } else {
            addSystemMessage(`❌ Ошибка загрузки файла: ${data.detail}`);
        }

    } catch (error) {
        console.error('Ошибка загрузки файла:', error);

        const uploadingMsg = document.getElementById('uploading-file');
        if (uploadingMsg) {
            uploadingMsg.remove();
        }

        addSystemMessage('❌ Ошибка загрузки файла');
    }
}

function addFileMessage(fileData, type) {
    const chatBox = document.getElementById('chatBox');
    const messageDiv = document.createElement('div');
    messageDiv.className = `file-message ${type}`;
    messageDiv.setAttribute('data-file-id', fileData.id);

    const fileIcon = getFileIcon(fileData.filename);
    const fileSize = formatFileSize(fileData.file_size);

    const statusText = fileData.status === 'pending'
        ? '⏳ На модерации'
        : fileData.status === 'approved'
        ? '✓ Одобрено'
        : '✗ Отклонено';

    messageDiv.innerHTML = `
        <div class="file-icon">${fileIcon}</div>
        <div class="file-name">${fileData.filename}</div>
        <div class="file-size">${fileSize}</div>
        <div class="file-status ${fileData.status}">${statusText}</div>
    `;

    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function getFileIcon(filename) {
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

function updateFileStatus(fileId, newStatus) {
    // Находим все карточки файлов в чате
    const fileMessages = document.querySelectorAll('.file-message');

    fileMessages.forEach(fileMsg => {
        const fileIdAttr = fileMsg.getAttribute('data-file-id');

        if (fileIdAttr == fileId) {
            // Обновляем статус
            const statusElement = fileMsg.querySelector('.file-status');
            if (statusElement) {
                statusElement.className = `file-status ${newStatus}`;

                const statusText = newStatus === 'approved'
                    ? '✓ Одобрено'
                    : newStatus === 'rejected'
                    ? '✗ Отклонено'
                    : '⏳ На модерации';

                statusElement.textContent = statusText;

                console.log(`✅ Статус файла ${fileId} обновлён на ${newStatus}`);
            }
        }
    });
}