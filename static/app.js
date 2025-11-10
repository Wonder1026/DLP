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

    ws.onmessage = function (event) {
        const data = JSON.parse(event.data);
        console.log('📨 Получено:', data);

        // Обработка ошибки (блокировка DLP)
        if (data.type === 'error') {
            addSystemMessage(data.message);
            return;
        }

        if (data.type === 'info') {
            addInfoMessage(data.message);
            return;
        }

        // Обработка предупреждения (конфиденциальные данные)
        if (data.type === 'warning') {
            addWarningMessage(data.message);
            return;
        }

        // Уведомление для админов
        if (data.type === 'admin_notification') {
            if (currentUser.is_admin) {
                showAdminNotification(data);
            }
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

    if (!text || !ws) {
        console.log('Нет текста или WebSocket не подключен');
        return;
    }

    console.log('Отправляем сообщение:', text);  // ← добавь эту строку для отладки

    // Отправляем через WebSocket
    const message = {
        user_id: currentUser.id,
        username: currentUser.username,
        user: currentUser.display_name,
        text: text,
        timestamp: new Date().toLocaleTimeString()
    };

    console.log('Данные для отправки:', message);  // ← добавь эту строку

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


let selectedFile = null;

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

    // Сохраняем файл и показываем модальное окно
    selectedFile = file;
    showModerationModal(file);

    // Очищаем input
    event.target.value = '';
}

function showModerationModal(file) {
    const modal = document.getElementById('moderationModal');
    const fileIcon = getFileIcon(file.name);
    const fileSize = formatFileSize(file.size);

    document.getElementById('modalFileIcon').textContent = fileIcon;
    document.getElementById('modalFileName').textContent = file.name;
    document.getElementById('modalFileSize').textContent = fileSize;

    modal.style.display = 'flex';
}

function cancelUpload() {
    const modal = document.getElementById('moderationModal');
    modal.style.display = 'none';
    selectedFile = null;
}

async function confirmUpload() {
    if (!selectedFile) return;

    const modal = document.getElementById('moderationModal');
    const moderationType = document.querySelector('input[name="moderationType"]:checked').value;

    modal.style.display = 'none';

    // Показываем сообщение о загрузке
    addFileUploadingMessage(selectedFile);

    // Загружаем файл с выбранным типом модерации
    await uploadFileWithModeration(selectedFile, moderationType);

    selectedFile = null;
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

async function uploadFileWithModeration(file, moderationType) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        // Имитация прогресса
        const progressBar = document.querySelector('#uploading-file .upload-progress-bar');
        if (progressBar) {
            progressBar.style.width = '50%';
        }

        const response = await fetch(`/api/files/upload?user_id=${currentUser.id}&moderation_type=${moderationType}`, {
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
            // Показываем системное сообщение о типе модерации
            const moderationText = moderationType === 'manual'
                ? '🛡️ Файл отправлен на ручную модерацию администратором'
                : '🌐 Файл отправлен на проверку через VirusTotal API';
            addSystemMessage(moderationText);

            // Добавляем сообщение об успешной загрузке себе
            addFileMessage(data.file, 'sent');

            // Отправляем уведомление ВСЕМ через WebSocket
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'file',
                    user_id: currentUser.id,
                    username: currentUser.username,
                    user: currentUser.display_name,
                    file: data.file
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

    // Кнопки действий для одобренных файлов
    let actionButtons = '';
    if (fileData.status === 'approved') {
        const isWordDoc = fileData.file_type === 'doc' || fileData.file_type === 'docx';

        actionButtons = `
            <div style="margin-top: 10px; display: flex; gap: 8px;">
                <button onclick="downloadFile(${fileData.id})" style="flex: 1; padding: 8px 12px; background: #28a745; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px;">
                    📥 Скачать
                </button>
                ${isWordDoc ? `
                <button onclick="previewFile(${fileData.id})" style="flex: 1; padding: 8px 12px; background: #17a2b8; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px;">
                    👁️ Предпросмотр
                </button>
                ` : ''}
            </div>
        `;
    }

    messageDiv.innerHTML = `
        <div class="file-icon">${fileIcon}</div>
        <div class="file-name">${fileData.filename}</div>
        <div class="file-size">${fileSize}</div>
        <div class="file-status ${fileData.status}">${statusText}</div>
        ${actionButtons}
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

function downloadFile(fileId) {
    const url = `/api/files/${fileId}/download?user_id=${currentUser.id}`;

    // Открываем в новом окне для скачивания
    window.open(url, '_blank');

    console.log(`📥 Скачивание файла ${fileId}`);
}

async function previewFile(fileId) {
    try {
        const response = await fetch(`/api/files/${fileId}/preview?user_id=${currentUser.id}`);
        const data = await response.json();

        if (response.ok) {
            showPreviewModal(data);
        } else {
            alert(`❌ ${data.detail}`);
        }

    } catch (error) {
        console.error('Ошибка предпросмотра:', error);
        alert('❌ Ошибка при загрузке предпросмотра');
    }
}

function showPreviewModal(previewData) {
    // Создаём модальное окно предпросмотра
    const modal = document.createElement('div');
    modal.id = 'previewModal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
    `;

    const content = document.createElement('div');
    content.style.cssText = `
        background: white;
        border-radius: 15px;
        padding: 30px;
        max-width: 800px;
        width: 100%;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    `;

    // Формируем HTML с содержимым документа
    let paragraphsHtml = '';
    previewData.paragraphs.forEach(para => {
        const fontSize = para.style.includes('Heading') ? '20px' : '14px';
        const fontWeight = para.style.includes('Heading') ? 'bold' : 'normal';

        paragraphsHtml += `
            <p style="margin-bottom: 12px; font-size: ${fontSize}; font-weight: ${fontWeight}; color: #333;">
                ${para.text}
            </p>
        `;
    });

    // Таблицы
    let tablesHtml = '';
    if (previewData.tables.length > 0) {
        tablesHtml = '<h3 style="margin-top: 20px; color: #667eea;">Таблицы:</h3>';
        previewData.tables.forEach((table, index) => {
            tablesHtml += `
                <table style="width: 100%; border-collapse: collapse; margin: 15px 0; border: 1px solid #ddd;">
                    ${table.map((row, rowIndex) => `
                        <tr style="background: ${rowIndex === 0 ? '#f8f9fa' : 'white'};">
                            ${row.map(cell => `
                                <td style="padding: 8px; border: 1px solid #ddd; font-size: 13px;">
                                    ${cell}
                                </td>
                            `).join('')}
                        </tr>
                    `).join('')}
                </table>
            `;
        });
    }

    content.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #667eea;">
            <div>
                <h2 style="color: #667eea; margin-bottom: 5px;">📄 ${previewData.filename}</h2>
                <p style="font-size: 13px; color: #999;">
                    Параграфов: ${previewData.paragraph_count} | Таблиц: ${previewData.table_count}
                </p>
            </div>
            <button onclick="closePreviewModal()" style="background: #dc3545; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 14px;">
                ✕ Закрыть
            </button>
        </div>
        
        <div style="color: #333; line-height: 1.6;">
            ${paragraphsHtml}
            ${tablesHtml}
        </div>
    `;

    modal.appendChild(content);
    document.body.appendChild(modal);

    // Закрытие по клику вне окна
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closePreviewModal();
        }
    });
}

function closePreviewModal() {
    const modal = document.getElementById('previewModal');
    if (modal) {
        modal.remove();
    }
}

function addWarningMessage(message) {
    const chatBox = document.getElementById('chatBox');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';
    messageDiv.style.background = '#fff3cd';
    messageDiv.style.borderLeft = '4px solid #ffc107';
    messageDiv.innerHTML = `<strong>⚠️ Предупреждение:</strong><br>${message}`;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function showAdminNotification(data) {
    // Создаём всплывающее уведомление для админа
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: ${data.is_banned ? '#dc3545' : '#ffc107'};
        color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        z-index: 9999;
        max-width: 350px;
        animation: slideIn 0.3s ease-out;
    `;

    notification.innerHTML = `
        <div style="font-weight: bold; margin-bottom: 10px; font-size: 16px;">
            ${data.is_banned ? '🚨 ПОЛЬЗОВАТЕЛЬ ЗАБЛОКИРОВАН' : '⚠️ ПРЕДУПРЕЖДЕНИЕ'}
        </div>
        <div style="margin-bottom: 10px;">
            <strong>Пользователь:</strong> ${data.display_name} (@${data.username})<br>
            <strong>Нарушений:</strong> ${data.violation_count}/10
        </div>
        ${data.is_banned ? `
            <button onclick="goToAdminPanel()" style="width: 100%; padding: 10px; background: white; color: #dc3545; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; margin-bottom: 5px;">
                Перейти в админку
            </button>
        ` : ''}
        <button onclick="this.parentElement.remove()" style="width: 100%; padding: 10px; background: rgba(255,255,255,0.3); color: white; border: none; border-radius: 5px; cursor: pointer;">
            Закрыть
        </button>
    `;

    document.body.appendChild(notification);

    // Автоматически удаляем через 10 секунд
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 10000);
}

function goToAdminPanel() {
    window.location.href = '/admin';
}

function addInfoMessage(message) {
    const chatBox = document.getElementById('chatBox');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';
    messageDiv.style.background = '#d1ecf1';
    messageDiv.style.borderLeft = '4px solid #17a2b8';
    messageDiv.innerHTML = `<strong>ℹ️ Информация:</strong><br>${message}`;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}