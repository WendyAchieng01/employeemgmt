let inactivityTimeout;

function resetInactivityTimer() {
    clearTimeout(inactivityTimeout);
    inactivityTimeout = setTimeout(() => {
        window.location.href = '/accounts/signout/'; // Redirect to signout view
    }, 20 * 60 * 1000); // 20 minutes in milliseconds
}

// Reset timer on user activity
['mousemove', 'keydown', 'click', 'scroll', 'touchstart'].forEach(event => {
    document.addEventListener(event, resetInactivityTimer);
});

// Start the timer when the page loads
resetInactivityTimer();