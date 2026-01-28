const AppNotifications = (function() {
    let toastContainer = null;

    function getToastContainer() {
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container';
            toastContainer.id = 'toast-container';
            document.body.appendChild(toastContainer);
        }
        return toastContainer;
    }

    const icons = {
        success: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
            <path d="M20 6L9 17l-5-5"/>
        </svg>`,
        error: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
        </svg>`,
        warning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 9v4m0 4h.01M12 3l9.5 16.5H2.5L12 3z"/>
        </svg>`,
        info: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 16v-4m0-4h.01"/>
        </svg>`
    };

    const titles = {
        success: 'Sucesso!',
        error: 'Erro!',
        warning: 'Atenção!',
        info: 'Informação'
    };

    function showToast(type, message, options = {}) {
        const container = getToastContainer();
        const duration = options.duration || 4000;
        const title = options.title || titles[type];

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-icon">
                ${icons[type]}
            </div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
            </button>
        `;

        container.appendChild(toast);

        if (duration > 0) {
            setTimeout(() => {
                toast.classList.add('toast-exit');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }

        return toast;
    }

    function success(message, options = {}) {
        return showToast('success', message, options);
    }

    function error(message, options = {}) {
        return showToast('error', message, options);
    }

    function warning(message, options = {}) {
        return showToast('warning', message, options);
    }

    function info(message, options = {}) {
        return showToast('info', message, options);
    }

    function confirm(options = {}) {
        return new Promise((resolve) => {
            const title = options.title || 'Confirmar ação';
            const message = options.message || 'Tem certeza que deseja continuar?';
            const confirmText = options.confirmText || 'Confirmar';
            const cancelText = options.cancelText || 'Cancelar';
            const type = options.type || 'warning';
            const confirmClass = options.confirmClass || (type === 'danger' ? 'btn-danger' : 'btn-primary');

            const iconClass = type === 'danger' ? 'icon-danger' : (type === 'info' ? 'icon-info' : 'icon-warning');

            const overlay = document.createElement('div');
            overlay.className = 'confirm-modal-overlay';
            overlay.innerHTML = `
                <div class="confirm-modal">
                    <div class="confirm-modal-header">
                        <div class="confirm-modal-icon ${iconClass}">
                            ${icons[type === 'danger' ? 'error' : type] || icons.warning}
                        </div>
                    </div>
                    <div class="confirm-modal-body">
                        <div class="confirm-modal-title">${title}</div>
                        <div class="confirm-modal-message">${message}</div>
                    </div>
                    <div class="confirm-modal-footer">
                        <button class="btn btn-secondary" id="confirm-cancel">${cancelText}</button>
                        <button class="btn ${confirmClass}" id="confirm-ok">${confirmText}</button>
                    </div>
                </div>
            `;

            document.body.appendChild(overlay);

            const cancelBtn = overlay.querySelector('#confirm-cancel');
            const confirmBtn = overlay.querySelector('#confirm-ok');

            function close(result) {
                overlay.style.animation = 'fadeOut 0.2s ease forwards';
                setTimeout(() => {
                    overlay.remove();
                    resolve(result);
                }, 200);
            }

            cancelBtn.onclick = () => close(false);
            confirmBtn.onclick = () => close(true);

            overlay.onclick = (e) => {
                if (e.target === overlay) close(false);
            };

            document.addEventListener('keydown', function escHandler(e) {
                if (e.key === 'Escape') {
                    document.removeEventListener('keydown', escHandler);
                    close(false);
                }
            });

            confirmBtn.focus();
        });
    }

    return {
        success,
        error,
        warning,
        info,
        confirm,
        showToast
    };
})();

window.toast = AppNotifications;
