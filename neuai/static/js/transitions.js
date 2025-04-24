document.addEventListener('DOMContentLoaded', function() {
    // Set the body to scale in when the page loads
    document.body.classList.add('scale-in');
    
    // Add scale transition effect to all links with the transition class
    const transitionLinks = document.querySelectorAll('.transition');
    
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
