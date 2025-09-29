// Debounce function to limit how often the search is performed
function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// Function to show loading state
function showLoading() {
    const playerDetails = document.getElementById('player-details');
    playerDetails.innerHTML = `
        <div class="mt-3 text-center text-muted">
            <div class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            Searching for player...
        </div>
    `;
}

// Function to show no results found
function showNoResults() {
    const playerDetails = document.getElementById('player-details');
    playerDetails.innerHTML = `
        <div class="alert alert-warning mt-3 mb-0">
            <i class="fas fa-exclamation-circle me-2"></i>
            No player found with this phone number. Please check and try again.
        </div>
    `;
}

// Function to perform the AJAX search
function searchPlayer(phoneNumber) {
    const playerDetails = document.getElementById('player-details');
    
    if (!phoneNumber) {
        playerDetails.innerHTML = '';
        return;
    }

    // Only search if we have exactly 10 digits
    if (phoneNumber.replace(/\D/g, '').length !== 10) {
        if (phoneNumber.length > 0) {
            playerDetails.innerHTML = `
                <div class="alert alert-info mt-3 mb-0">
                    <i class="fas fa-info-circle me-2"></i>
                    Please enter a valid 10-digit phone number
                </div>
            `;
        }
        return;
    }

    showLoading();

    // Use the correct URL pattern
    const searchUrl = document.querySelector('form').dataset.searchUrl || '/teams/search_player/';
    fetch(`${searchUrl}?phone_number=${encodeURIComponent(phoneNumber)}`)
        .then(response => response.text())
        .then(html => {
            if (html.trim() === '') {
                showNoResults();
            } else {
                playerDetails.innerHTML = html;
            }
        })
        .catch(error => {
            console.error('Error searching for player:', error);
            playerDetails.innerHTML = `
                <div class="alert alert-danger mt-3 mb-0">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    An error occurred while searching. Please try again.
                </div>
            `;
        });
}

// Set up event listener when the document is loaded
document.addEventListener('DOMContentLoaded', function() {
    const phoneInput = document.getElementById('id_phone_number');
    if (phoneInput) {
        // Use debounce to prevent flickering - only search after 300ms of no typing
        const debouncedSearch = debounce(searchPlayer, 300);
        
        phoneInput.addEventListener('input', function(e) {
            debouncedSearch(e.target.value);
        });
    }
});