document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.querySelector('.login-form');
    const registerForm = document.querySelector('.register-form');

    // Client-side form validation
    function validateForm(form, isLogin = true) {
        const username = form.querySelector('input[name="username"]');
        const password = form.querySelector('input[name="password"]');
        const passwordConfirm = isLogin ? null : form.querySelector('input[name="confirm_password"]');

        // Reset previous error styles
        username.classList.remove('error');
        password.classList.remove('error');
        if (passwordConfirm) passwordConfirm.classList.remove('error');

        // Validation checks
        let isValid = true;

        if (username.value.trim().length < 3) {
            username.classList.add('error');
            isValid = false;
        }

        if (password.value.length < 6) {
            password.classList.add('error');
            isValid = false;
        }

        if (!isLogin && password.value !== passwordConfirm.value) {
            password.classList.add('error');
            passwordConfirm.classList.add('error');
            isValid = false;
        }

        return isValid;
    }

    // Add validation to login form if exists
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            if (!validateForm(loginForm)) {
                e.preventDefault();
            }
        });
    }

    // Add validation to register form if exists
    if (registerForm) {
        registerForm.addEventListener('submit', (e) => {
            if (!validateForm(registerForm, false)) {
                e.preventDefault();
            }
        });
    }

    // Optional: Password visibility toggle
    const passwordToggle = document.querySelector('.password-toggle');
    if (passwordToggle) {
        passwordToggle.addEventListener('click', () => {
            const passwordInput = document.querySelector('input[name="password"]');
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
        });
    }
});