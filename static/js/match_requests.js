// Match request functionality
// Utility function to safely get CSRF token
function getCsrfToken() {
    // First try to get from input element
    const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (tokenInput) return tokenInput.value;
    
    // Fallback to cookie
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', function() {
    const callMatchForm = document.getElementById('callMatchForm');
    const facilitySelect = document.getElementById('facility');
    const timeSlotSelect = document.getElementById('timeSlot');
    const dateInput = document.getElementById('matchDate');

    if (callMatchForm) {
        // Handle form submission
        callMatchForm.addEventListener('submit', function(e) {
            e.preventDefault();

            // Get form data
            const formData = new FormData(this);

            // Send request
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCsrfToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, 'success');
                    bootstrap.Modal.getInstance(document.getElementById('callMatchModal')).hide();
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showToast(data.message || 'Error sending match request', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error sending match request', 'error');
            });
        });

        // Handle facility selection
        if (facilitySelect && timeSlotSelect && dateInput) {
            facilitySelect.addEventListener('change', function() {
                timeSlotSelect.disabled = !this.value;
                if (this.value && dateInput.value) {
                    fetchTimeSlots();
                }
            });

            dateInput.addEventListener('change', function() {
                if (facilitySelect.value) {
                    fetchTimeSlots();
                }
            });
        }
    }

    // Fetch available time slots
    function fetchTimeSlots() {
        const facilityId = facilitySelect.value;
        const date = dateInput.value;

        if (!facilityId || !date) return;

        const formattedDate = new Date(date).toISOString().split('T')[0];
        fetch(`/facilities/get-slots/?facility_id=${facilityId}&date=${formattedDate}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                timeSlotSelect.innerHTML = '<option value="">Choose a time slot...</option>';
                if (data.slots && Array.isArray(data.slots)) {
                    data.slots.forEach(slot => {
                        if (slot.is_available) {
                            const option = document.createElement('option');
                            option.value = slot.id;
                            option.textContent = slot.display_time;
                            timeSlotSelect.appendChild(option);
                        }
                    });
                }
                timeSlotSelect.disabled = false;
            })
            .catch(error => {
                console.error('Error fetching slots:', error);
                showToast('Error: ' + error.message, 'error');
                timeSlotSelect.disabled = true;
            })
            .catch(error => {
                console.error('Error fetching time slots:', error);
                showToast('Error fetching time slots', 'error');
            });
    }

    // Show toast messages
    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast position-fixed bottom-0 end-0 m-4 text-white bg-${type === 'success' ? 'success' : 'danger'}`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `<div class="toast-body">${message}</div>`;
        document.body.appendChild(toast);
        new bootstrap.Toast(toast).show();
        setTimeout(() => toast.remove(), 3000);
    }
});