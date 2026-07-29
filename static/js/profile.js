document.addEventListener('DOMContentLoaded', () => {
    const avatarSelect = document.getElementById('chosen_avatar');
    const validateBtn = document.getElementById('validate-avatar-btn');
    const indicator = document.getElementById('mini-save-indicator');
    
    if (!avatarSelect || !validateBtn) return;

    const originalAvatar = avatarSelect.value;

    avatarSelect.addEventListener('change', function() {
        const pendingAvatar = this.value;

        document.getElementById('profile-card-avatar').src = '/static/image/avatars/' + pendingAvatar;

        if (pendingAvatar !== originalAvatar) {
            validateBtn.style.display = 'inline-flex';
            indicator.style.display = 'none';
        } else {
            validateBtn.style.display = 'none';
        }
    });
});