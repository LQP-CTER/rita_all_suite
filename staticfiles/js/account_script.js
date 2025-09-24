document.addEventListener('DOMContentLoaded', function() {
    /**
     * DOM Elements
     */
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const loginContent = document.getElementById('login-content');
    const registerContent = document.getElementById('register-content');
    const signInForm = document.getElementById('sign-in-form');
    const signUpForm = document.getElementById('sign-up-form');
    const signInError = document.getElementById('signInError');
    const signUpMessage = document.getElementById('signUpMessage');

    /**
     * Tab switching functionality
     */
    if (tabLogin && tabRegister && loginContent && registerContent) {
        tabLogin.addEventListener('click', () => {
            tabLogin.classList.add('active');
            tabRegister.classList.remove('active');
            loginContent.classList.add('active');
            registerContent.classList.remove('active');
        });

        tabRegister.addEventListener('click', () => {
            tabRegister.classList.add('active');
            tabLogin.classList.remove('active');
            registerContent.classList.add('active');
            loginContent.classList.remove('active');
        });
    }

    /**
     * Sign In Form Submission (AJAX)
     */
    if (signInForm) {
        signInForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            if(signInError) signInError.textContent = '';

            const formData = new FormData(signInForm);
            
            try {
                const response = await fetch(signInForm.action, {
                    method: 'POST',
                    body: new URLSearchParams(formData)
                });

                const result = await response.json();

                if (response.ok && result.status === 'success') {
                    window.location.href = result.redirect_url;
                } else {
                    if(signInError) signInError.textContent = result.message || 'Đã có lỗi xảy ra.';
                }
            } catch (error) {
                if(signInError) signInError.textContent = 'Lỗi kết nối đến server.';
            }
        });
    }

    /**
     * Sign Up Form Submission (AJAX)
     */
    if (signUpForm) {
        signUpForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            if(signUpMessage) {
                signUpMessage.textContent = '';
                signUpMessage.className = 'message-container message'; // Reset class
            }
            
            // Clear previous errors
            document.querySelectorAll('.field-error').forEach(el => el.textContent = '');

            const formData = new FormData(signUpForm);
            
            try {
                const response = await fetch(signUpForm.action, {
                    method: 'POST',
                    body: formData,
                });

                const result = await response.json();

                if (response.ok && result.status === 'success') {
                    window.location.href = result.redirect_url;
                } else {
                    if(signUpMessage) {
                        signUpMessage.textContent = 'Vui lòng sửa các lỗi bên dưới.';
                        signUpMessage.classList.add('error');
                    }
                    
                    if (result.errors) {
                        const errors = JSON.parse(result.errors);
                        for (const field in errors) {
                            const errorDiv = document.getElementById(`${field}-error`);
                            if (errorDiv) {
                                errorDiv.textContent = errors[field][0].message;
                            } else if (field === '__all__') {
                                // For non-field errors like password mismatch
                                const confirmPasswordErrorDiv = document.getElementById('password2-error');
                                if (confirmPasswordErrorDiv) {
                                    confirmPasswordErrorDiv.textContent = errors[field][0].message;
                                }
                            }
                        }
                    } else if (result.message) {
                        signUpMessage.textContent = result.message;
                        signUpMessage.classList.add('error');
                    }
                }
            } catch (error) {
                if(signUpMessage) {
                    signUpMessage.textContent = 'Lỗi kết nối đến server.';
                    signUpMessage.classList.add('error');
                }
            }
        });
    }
});