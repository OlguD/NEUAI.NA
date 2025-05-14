/**
 * Password Toggle Functionality
 * This script handles the password visibility toggle on the login page
 */

// Execute when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get required elements
    const passwordInput = document.getElementById('passwordInput');
    const passwordToggle = document.getElementById('passwordToggle');
    const passwordToggleIcon = document.getElementById('passwordToggleIcon');
    
    console.log('Password toggle script loaded');
    
    // Make sure required elements exist
    if (!passwordToggle || !passwordInput || !passwordToggleIcon) {
        console.error('Password toggle elements missing!');
        return;
    }
    
    // Add direct click handler
    passwordToggle.onclick = function(event) {
        // Prevent any default action and stop event propagation
        event.preventDefault();
        event.stopPropagation();
        
        console.log('Toggle button clicked');
        
        // Toggle password visibility
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            passwordToggleIcon.className = 'fas fa-eye-slash';
        } else {
            passwordInput.type = 'password';
            passwordToggleIcon.className = 'fas fa-eye';
        }
        
        // Return focus to input
        passwordInput.focus();
    };
});
