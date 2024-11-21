let deferredPrompt; 

// Listen for the 'beforeinstallprompt' event
window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the mini-infobar from appearing
    e.preventDefault(); 
    // Save the event for later use
    deferredPrompt = e;

    // Show the install prompt
    const installPrompt = document.getElementById('install-prompt');
    installPrompt.style.display = 'block';

    // Handle the install button click
    const installButton = document.getElementById('install-btn');
    installButton.addEventListener('click', () => {
        // Show the install prompt
        deferredPrompt.prompt();

        // Handle the user's response to the install prompt
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('User accepted the install prompt');
            } else {
                console.log('User dismissed the install prompt');
            }
            deferredPrompt = null;
            installPrompt.style.display = 'none'; // Hide the prompt after response
        });
    });

    // Handle the cancel button click
    const cancelButton = document.getElementById('cancel-btn');
    cancelButton.addEventListener('click', () => {
        installPrompt.style.display = 'none'; // Hide the prompt
    });
});

// Hide the install prompt once the app is installed
window.addEventListener('appinstalled', () => {
    console.log('PWA installed');
    document.getElementById('install-prompt').style.display = 'none'; // Hide after install
});
