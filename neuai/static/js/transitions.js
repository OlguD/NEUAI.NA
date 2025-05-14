document.addEventListener('DOMContentLoaded', function() {
    // Set the body to scale in when the page loads
    document.body.classList.add('scale-in');
    
    // Get password form and error message elements
    const passwordForm = document.getElementById('passwordForm');
    const passwordInput = document.getElementById('passwordInput');
    const errorMessage = document.getElementById('errorMessage');
    
    // Add password validation
    if (passwordForm) {
        passwordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Check if password is correct (1408)
            if (passwordInput.value === '1408') {
                // Start scale out animation
                document.body.classList.add('scale-out');
                document.body.classList.remove('scale-in');
                
                // Wait for animation to complete
                setTimeout(function() {
                    // Get redirect URL from the form's data attribute
                    const redirectUrl = passwordForm.getAttribute('data-redirect') || '/index';
                    window.location.href = redirectUrl;
                }, 500); // Match this time with CSS transition duration
            } else {
                // Show error message
                errorMessage.style.visibility = 'visible';
                
                // Clear password input
                passwordInput.value = '';
                passwordInput.focus();
                
                // Hide error message after 3 seconds
                setTimeout(function() {
                    errorMessage.style.visibility = 'hidden';
                }, 3000);
            }
        });
        
        // Enable numeric input only
        passwordInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
        });
    }
    
    // For other transition links besides the password form
    const transitionLinks = document.querySelectorAll('.transition:not(button)');
    
    transitionLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetUrl = this.getAttribute('href');
            
            // Start scale out
            document.body.classList.add('scale-out');
            document.body.classList.remove('scale-in');
            
            // Wait for animation to complete
            setTimeout(function() {
                window.location.href = targetUrl;
            }, 500); // Match this time with CSS transition duration
        });
    });
});
