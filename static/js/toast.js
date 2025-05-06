function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type} toast-enter`;
    
    // Create content
    let description = '';
    let icon = '';
    
    // Set icon based on type
    switch(type) {
        case 'success':
            icon = '<i class="ri-checkbox-circle-line text-lg"></i>';
            break;
        case 'info':
            icon = '<i class="ri-information-line text-lg"></i>';
            break;
        case 'warning':
            icon = '<i class="ri-alert-line text-lg"></i>';
            break;
        case 'destructive':
            icon = '<i class="ri-error-warning-line text-lg"></i>';
            break;
        default:
            icon = '<i class="ri-checkbox-circle-line text-lg"></i>';
    }
    
    // Handle both string and object messages
    if (typeof message === 'object') {
        if (message.errors) {
            // Get the first error message
            description = Object.values(message.errors)[0][0];
            type = 'destructive';
            icon = '<i class="ri-error-warning-line text-lg"></i>';
        } else {
            description = message.message || 'An error occurred';
        }
    } else {
        description = message;
    }

    // Create toast content
    toast.innerHTML = `
        <div class="flex items-center gap-3">
            <div class="flex-shrink-0">
                ${icon}
            </div>
            <div class="toast-description flex-1">${description}</div>
            <button class="toast-close flex-shrink-0" onclick="this.parentElement.parentElement.classList.add('toast-exit'); setTimeout(() => this.parentElement.parentElement.remove(), 200)">
                <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M11.7816 4.03157C12.0062 3.80702 12.0062 3.44295 11.7816 3.2184C11.5571 2.99385 11.193 2.99385 10.9685 3.2184L7.50005 6.68682L4.03164 3.2184C3.80708 2.99385 3.44301 2.99385 3.21846 3.2184C2.99391 3.44295 2.99391 3.80702 3.21846 4.03157L6.68688 7.49999L3.21846 10.9684C2.99391 11.193 2.99391 11.557 3.21846 11.7816C3.44301 12.0061 3.80708 12.0061 4.03164 11.7816L7.50005 8.31316L10.9685 11.7816C11.193 12.0061 11.5571 12.0061 11.7816 11.7816C12.0062 11.557 12.0062 11.193 11.7816 10.9684L8.31322 7.49999L11.7816 4.03157Z" fill="currentColor" fill-rule="evenodd" clip-rule="evenodd"></path>
                </svg>
            </button>
        </div>
    `;
    
    // Get or create toast viewport
    let viewport = document.querySelector('.toast-viewport');
    if (!viewport) {
        viewport = document.createElement('div');
        viewport.className = 'toast-viewport';
        document.body.appendChild(viewport);
    }
    
    // Add toast to viewport
    viewport.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 200);
    }, 5000);
}

// Alias for backward compatibility
function showNotification(title, message, type = 'success') {
    showToast(message, type);
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { showToast, showNotification };
} 