function switchTab(tab) {
    // Переключение табов
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.form-container').forEach(f => f.classList.remove('active'));

    if (tab === 'login') {
        document.querySelectorAll('.tab')[0].classList.add('active');
        document.getElementById('loginForm').classList.add('active');
    } else {
        document.querySelectorAll('.tab')[1].classList.add('active');
        document.getElementById('registerForm').classList.add('active');
    }

    hideMessages();
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

async function handleLogin(event) {
    event.preventDefault();
    hideMessages();

    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Сохраняем данные пользователя
            localStorage.setItem('user', JSON.stringify(data.user));

            showSuccess('Вход выполнен! Перенаправление...');

            // Переход в чат через 1 секунду
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);

        } else {
            showError(data.detail || 'Ошибка входа');
        }

    } catch (error) {
        console.error('Ошибка:', error);
        showError('Ошибка соединения с сервером');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    hideMessages();

    const username = document.getElementById('registerUsername').value;
    const displayName = document.getElementById('registerDisplayName').value;
    const password = document.getElementById('registerPassword').value;

    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                display_name: displayName,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess('Регистрация успешна! Теперь войдите.');

            // Очищаем форму
            document.getElementById('registerUsername').value = '';
            document.getElementById('registerDisplayName').value = '';
            document.getElementById('registerPassword').value = '';

            // Переключаемся на вход через 2 секунды
            setTimeout(() => {
                switchTab('login');
                document.getElementById('loginUsername').value = username;
            }, 2000);

        } else {
            showError(data.detail || 'Ошибка регистрации');
        }

    } catch (error) {
        console.error('Ошибка:', error);
        showError('Ошибка соединения с сервером');
    }
}