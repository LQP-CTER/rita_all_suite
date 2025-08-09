document.addEventListener('DOMContentLoaded', function() {
    /**
     * DOM Elements
     */
    const signupButton = document.getElementById('signup-button');
    const loginButton = document.getElementById('login-button');
    const userForms = document.getElementById('user_options-forms');
    const signInForm = document.getElementById('sign-in-form');
    const signUpForm = document.getElementById('sign-up-form');
    const signInError = document.getElementById('signInError');
    const signUpMessage = document.getElementById('signUpMessage');
    const clockContainer = document.getElementById('live-clock-container');

    /**
     * Toggling between Login and Signup forms
     */
    if (signupButton) {
        signupButton.addEventListener('click', () => {
            userForms.classList.remove('bounceRight');
            userForms.classList.add('bounceLeft');
        }, false);
    }

    if (loginButton) {
        loginButton.addEventListener('click', () => {
            userForms.classList.remove('bounceLeft');
            userForms.classList.add('bounceRight');
        }, false);
    }

    /**
     * Live Clock Functionality
     */
    function updateClock() {
        if (clockContainer) {
            const now = new Date();
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const seconds = String(now.getSeconds()).padStart(2, '0');
            clockContainer.textContent = `${hours}:${minutes}:${seconds}`;
        }
    }
    // Update the clock every second
    setInterval(updateClock, 1000);
    // Initial call to display clock immediately
    updateClock();


    /**
     * Sign In Form Submission
     */
    async function handleSignIn(e) {
        e.preventDefault();
        signInError.textContent = '';
        const formData = new FormData(signInForm);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch(signInForm.action || window.location.href, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': data.csrfmiddlewaretoken
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok && result.status === 'success') {
                window.location.href = result.redirect_url;
            } else {
                signInError.textContent = result.message || 'Đã có lỗi xảy ra.';
            }
        } catch (error) {
            signInError.textContent = 'Lỗi kết nối đến server.';
        }
    }

    /**
     * Sign Up Form Submission
     */
    async function handleSignUp(e) {
        e.preventDefault();
        signUpMessage.textContent = '';
        signUpMessage.className = 'message-container message'; // Reset class
        
        // Clear previous errors
        document.querySelectorAll('.field-error').forEach(el => el.textContent = '');

        const formData = new FormData(signUpForm);
        
        try {
            const response = await fetch(signUpForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            });

            const result = await response.json();

            if (response.ok && result.status === 'success') {
                signUpMessage.textContent = result.message;
                signUpMessage.classList.add('success');
                signUpForm.reset();
                // Optional: Automatically switch to login form after successful registration
                setTimeout(() => {
                    loginButton.click();
                }, 2000);
            } else {
                signUpMessage.textContent = 'Vui lòng sửa các lỗi bên dưới.';
                signUpMessage.classList.add('error');
                
                if (result.errors) {
                    const errors = JSON.parse(result.errors);
                    for (const field in errors) {
                        const errorDiv = document.getElementById(`${field}-error`);
                        if (errorDiv) {
                            errorDiv.textContent = errors[field][0].message;
                        } else if (field === '__all__') {
                            document.getElementById('confirm_password-error').textContent = errors[field][0].message;
                        }
                    }
                }
            }
        } catch (error) {
            signUpMessage.textContent = 'Lỗi kết nối đến server.';
            signUpMessage.classList.add('error');
        }
    }

    if (signInForm) {
        signInForm.addEventListener('submit', handleSignIn);
    }
    if (signUpForm) {
        signUpForm.addEventListener('submit', handleSignUp);
    }
});
