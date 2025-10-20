let currentUser = null;

window.addEventListener('load', function() {
    // Проверка авторизации
    const userData = localStorage.getItem('user');

    if (!userData) {
        window.location.href = '/login';
        return;
    }

    currentUser = JSON.parse(userData);
    loadUserProfile();
});

function loadUserProfile() {
    // Заполняем форму данными пользователя
    document.getElementById('username').value = currentUser.username;
    document.getElementById('displayName').value = currentUser.display_name;

    // Отображаем роль
    if (currentUser.is_super_admin) {
        document.getElementById('role').value = 'Главный Администратор';
        document.getElementById('roleBadge').textContent = 'SUPER ADMIN';
        document.getElementById('roleBadge').style.background = '#dc3545';
        document.getElementById('roleBadge').style.color = 'white';
    } else if (currentUser.is_admin) {
        document.getElementById('role').value = 'Администратор';
        document.getElementById('roleBadge').textContent = 'Администратор';
        document.getElementById('roleBadge').style.background = '#fff3cd';
        document.getElementById('roleBadge').style.color = '#856404';
    }

    // Инициалы для аватара
    const initial = currentUser.display_name.charAt(0).toUpperCase();
    document.getElementById('avatarInitial').textContent = initial;
}

async function handleUpdateProfile(event) {
    event.preventDefault();
    hideMessages();

    const displayName = document.getElementById('displayName').value.trim();

    if (!displayName) {
        showError('Введите отображаемое имя');
        return;
    }

    try {
        const response = await fetch(`/api/auth/profile?user_id=${currentUser.id}&display_name=${encodeURIComponent(displayName)}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (response.ok) {
            // Обновляем данные в localStorage
            currentUser.display_name = data.user.display_name;
            localStorage.setItem('user', JSON.stringify(data.user));

            showSuccess('✅ Профиль успешно обновлён!');

            // Обновляем инициал
            const initial = displayName.charAt(0).toUpperCase();
            document.getElementById('avatarInitial').textContent = initial;

        } else {
            showError(data.detail || 'Ошибка обновления профиля');
        }

    } catch (error) {
        console.error('Ошибка:', error);
        showError('Ошибка соединения с сервером');
    }
}

function handleAvatarUpload(event) {
    // Пока просто показываем, что функция в разработке
    showError('Загрузка фото будет доступна в следующей версии');
}

function showError(message) {
    const errorDiv = document.getElementById('errorMsg');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    document.getElementById('successMsg').style.display = 'none';
}

function showSuccess(message) {
    const successDiv = document.getElementById('successMsg');
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    document.getElementById('errorMsg').style.display = 'none';
}

function hideMessages() {
    document.getElementById('errorMsg').style.display = 'none';
    document.getElementById('successMsg').style.display = 'none';
}