document.addEventListener('DOMContentLoaded', function() {
    const dateTabs = document.querySelectorAll('.date-tab');

    dateTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Remove active class from all tabs
            dateTabs.forEach(t => t.classList.remove('active'));
            
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Show loading state
            const slotsContainer = document.querySelector('.slots-container');
            if (slotsContainer) {
                slotsContainer.innerHTML = `
                    <div class="text-center p-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p class="mt-3">Loading available slots...</p>
                    </div>
                `;
            }

            // Fetch slots for selected date via AJAX
            fetch(`/bookings/get-slots/?date=${this.dataset.date}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.text();
                })
                .then(html => {
                    if (slotsContainer) {
                        slotsContainer.innerHTML = html;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    if (slotsContainer) {
                        slotsContainer.innerHTML = `
                            <div class="alert alert-danger text-center" role="alert">
                                <i class="fas fa-exclamation-circle me-2"></i>
                                Error loading slots. Please try again.
                            </div>
                        `;
                    }
                });
        });
    });
});