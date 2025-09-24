document.addEventListener('DOMContentLoaded', () => {
    const authCard = document.querySelector('.auth-card');
    const tabButtons = document.querySelectorAll('[data-auth-tab]');
    const panels = document.querySelectorAll('.auth-panel');

    const activateTab = (target) => {
        tabButtons.forEach(btn => {
            const isActive = btn.dataset.authTab === target;
            btn.classList.toggle('active', isActive);
        });
        panels.forEach(panel => {
            const isActive = panel.dataset.authPanel === target;
            panel.classList.toggle('active', isActive);
        });
    };

    if (tabButtons.length && panels.length) {
        const initial = authCard?.dataset?.initialTab || tabButtons[0].dataset.authTab;
        activateTab(initial);

        tabButtons.forEach(btn => {
            btn.addEventListener('click', () => activateTab(btn.dataset.authTab));
        });
    }

    const signInForm = document.getElementById('sign-in-form');
    const signUpForm = document.getElementById('sign-up-form');
    const signInError = document.getElementById('signInError');
    const signUpMessage = document.getElementById('signUpMessage');

    if (signInForm) {
        signInForm.addEventListener('submit', async (event) => {
            if (!signInForm.dataset.ajax) return;
            event.preventDefault();
            if (signInError) signInError.textContent = '';

            const formData = new FormData(signInForm);
            try {
                const response = await fetch(signInForm.action, {
                    method: 'POST',
                    body: new URLSearchParams(formData),
                });
                const result = await response.json();

                if (response.ok && result.status === 'success') {
                    window.location.href = result.redirect_url;
                } else if (signInError) {
                    signInError.textContent = result.message || 'Đăng nhập không thành công.';
                }
            } catch (error) {
                if (signInError) signInError.textContent = 'Không thể kết nối tới máy chủ.';
            }
        }, { once: false });
    }

    if (signUpForm) {
        signUpForm.addEventListener('submit', async (event) => {
            if (!signUpForm.dataset.ajax) return;
            event.preventDefault();
            if (signUpMessage) {
                signUpMessage.textContent = '';
                signUpMessage.className = 'form-feedback';
            }
            document.querySelectorAll('.form-error[id$="-error"]').forEach(el => el.textContent = '');

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
                    if (signUpMessage) {
                        signUpMessage.textContent = 'Vui lòng kiểm tra lại các trường thông tin.';
                        signUpMessage.classList.add('form-feedback-error');
                    }
                    if (result.errors) {
                        try {
                            const errors = JSON.parse(result.errors);
                            Object.entries(errors).forEach(([field, messages]) => {
                                const container = document.getElementById(`${field}-error`);
                                if (container && messages.length) {
                                    container.textContent = messages[0].message || messages[0];
                                }
                            });
                        } catch (e) {
                            // ignore JSON parse errors
                        }
                    }
                }
            } catch (error) {
                if (signUpMessage) {
                    signUpMessage.textContent = 'Không thể kết nối tới máy chủ.';
                    signUpMessage.classList.add('form-feedback-error');
                }
            }
        }, { once: false });
    }
});
