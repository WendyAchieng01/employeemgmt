let inactivityTimeout;
        const inactivityPeriod = 20 * 60 * 1000; // 20 minutes in milliseconds

        function resetInactivityTimer() {
            clearTimeout(inactivityTimeout);
            
            // Update timer display
            updateTimerDisplay();
            
            inactivityTimeout = setTimeout(() => {
                // Store the current URL before redirecting
                const returnUrl = window.location.href;
                sessionStorage.setItem('returnUrl', returnUrl);
                
                document.getElementById('demo-message').textContent = 
                    `Would redirect to: /accounts/signout/?next=${encodeURIComponent(returnUrl)}`;
                
                // In a real scenario, you would redirect here
                // window.location.href = `/accounts/signout/?next=${encodeURIComponent(returnUrl)}`;
            }, 10000); // Using 10 seconds for demo purposes
        }

        // Function to update timer display
        function updateTimerDisplay() {
            clearInterval(window.timerInterval);
            
            window.timerInterval = setInterval(() => {
                if (inactivityTimeout) {
                    const remaining = inactivityTimeout._idleStart + 10000 - Date.now();
                    if (remaining > 0) {
                        const seconds = Math.floor(remaining / 1000);
                        document.getElementById('timer').textContent = 
                            `00:${seconds.toString().padStart(2, '0')}`;
                    }
                }
            }, 200);
        }

        // Reset timer on user activity
        ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, resetInactivityTimer);
        });

        // Manual logout function that preserves return URL
        function manualLogout() {
            const returnUrl = window.location.href;
            sessionStorage.setItem('returnUrl', returnUrl);
            document.getElementById('demo-message').textContent = 
                `Would redirect to: /accounts/signout/?next=${encodeURIComponent(returnUrl)}`;
        }

        // Start the timer when the page loads
        window.addEventListener('load', resetInactivityTimer);