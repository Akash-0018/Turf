// Utility function to get CSRF token
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
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

// Reset form state
function resetForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        // Reset form fields
        form.reset();
        
        // Reset form mode and IDs
        form.dataset.mode = 'add';
        delete form.dataset.facilityId;
        delete form.dataset.sportId;
        delete form.dataset.offerId;
        
        // Reset Select2 if exists
        const select2Elements = form.querySelectorAll('.select2');
        select2Elements.forEach(select => {
            $(select).val(null).trigger('change');
        });
        
        // Reset modal title
        const modalTitle = form.closest('.modal')?.querySelector('.modal-title');
        if (modalTitle) {
            modalTitle.textContent = `Add New ${formId.replace('Form', '')}`;
        }
        
        // Reset any custom validation states
        form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        form.querySelectorAll('.invalid-feedback').forEach(el => el.textContent = '');
    }
}

// Facility Management
document.querySelectorAll('.edit-facility').forEach(button => {
    button.addEventListener('click', function() {
        const facilityId = this.dataset.id;
        const form = document.getElementById('facilityForm');
        
        // Get facility data
        fetch(`/facilities/admin/facility/${facilityId}/edit/`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            // Set form to edit mode
            form.dataset.mode = 'edit';
            form.dataset.facilityId = facilityId;
            
            // Update form fields
            form.querySelector('[name="name"]').value = data.name;
            form.querySelector('[name="description"]').value = data.description;
            form.querySelector('[name="location"]').value = data.location;
            form.querySelector('[name="latitude"]').value = data.latitude || '';
            form.querySelector('[name="longitude"]').value = data.longitude || '';
            form.querySelector('[name="rules"]').value = data.rules || '';
            form.querySelector('[name="opening_time"]').value = data.opening_time;
            form.querySelector('[name="closing_time"]').value = data.closing_time;
            form.querySelector('[name="is_active"]').checked = data.is_active;

            // Update amenities
            const amenitiesSelect = form.querySelector('[name="amenities[]"]');
            if (amenitiesSelect) {
                $(amenitiesSelect).val(data.amenities).trigger('change');
            }
            
            // Ensure the checkbox value is properly set
            const isActiveCheckbox = form.querySelector('[name="is_active"]');
            if (isActiveCheckbox) {
                isActiveCheckbox.checked = Boolean(data.is_active);
            }
            
            // Update modal title
            const modalTitle = form.closest('.modal').querySelector('.modal-title');
            modalTitle.textContent = 'Edit Facility';
            
            // Show modal
            new bootstrap.Modal(document.getElementById('addFacilityModal')).show();
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error loading facility data', 'error');
        });
    });
});

// Sport Management
document.querySelectorAll('.edit-sport').forEach(button => {
    button.addEventListener('click', function() {
        const sportId = this.dataset.id;
        const form = document.getElementById('sportForm');
        
        fetch(`/facilities/admin/sport/${sportId}/edit/`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            // Set form to edit mode
            form.dataset.mode = 'edit';
            form.dataset.sportId = sportId;
            
            // Update form fields
            form.querySelector('[name="name"]').value = data.name;
            
            // Update modal title
            const modalTitle = form.closest('.modal').querySelector('.modal-title');
            modalTitle.textContent = 'Edit Sport';
            
            // Show modal
            new bootstrap.Modal(document.getElementById('addSportModal')).show();
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error loading sport data', 'error');
        });
    });
});

// Offer Management
document.querySelectorAll('.edit-offer').forEach(button => {
    button.addEventListener('click', function() {
        const offerId = this.dataset.id;
        const form = document.getElementById('offerForm');
        
        fetch(`/facilities/admin/offer/${offerId}/edit/`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            // Set form to edit mode
            form.dataset.mode = 'edit';
            form.dataset.offerId = offerId;
            
            // Update form fields
            form.querySelector('[name="facility"]').value = data.facility;
            form.querySelector('[name="title"]').value = data.title;
            form.querySelector('[name="description"]').value = data.description;
            form.querySelector('[name="discount_percentage"]').value = data.discount_percentage;
            form.querySelector('[name="start_date"]').value = data.start_date;
            form.querySelector('[name="end_date"]').value = data.end_date;
            form.querySelector('[name="is_active"]').checked = data.is_active;
            
            // Update modal title
            const modalTitle = form.closest('.modal').querySelector('.modal-title');
            modalTitle.textContent = 'Edit Offer';
            
            // Show modal
            new bootstrap.Modal(document.getElementById('addOfferModal')).show();
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error loading offer data', 'error');
        });
    });
});

// Form Submissions
['facilityForm', 'sportForm', 'offerForm'].forEach(formId => {
    const form = document.getElementById(formId);
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const mode = this.dataset.mode || 'add';
            const type = formId.replace('Form', '').toLowerCase();
            let id = null;
            
            // Get the correct ID based on type
            switch(type) {
                case 'facility':
                    id = this.dataset.facilityId;
                    break;
                case 'sport':
                    id = this.dataset.sportId;
                    break;
                case 'offer':
                    id = this.dataset.offerId;
                    break;
            }
            
            const url = mode === 'edit' && id ? 
                `/facilities/admin/${type}/${id}/edit/` : 
                `/facilities/admin/${type}/add/`;
            
            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message || `${type} ${mode === 'edit' ? 'updated' : 'added'} successfully`);
                    location.reload();
                } else {
                    showToast(data.message || `Error ${mode === 'edit' ? 'updating' : 'adding'} ${type}`, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast(`Error ${mode === 'edit' ? 'updating' : 'adding'} ${type}`, 'error');
            });
        });
    }
});

// Toggle handlers
document.querySelectorAll('.toggle-offer').forEach(toggle => {
    toggle.addEventListener('change', function() {
        const offerId = this.dataset.id;
        const isActive = this.checked;
        
        fetch(`/facilities/admin/offer/${offerId}/toggle/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast(data.message || 'Offer updated successfully');
            } else {
                showToast(data.message || 'Error updating offer', 'error');
                this.checked = !isActive;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error updating offer', 'error');
            this.checked = !isActive;
        });
    });
});

// Delete handlers
document.querySelectorAll('[data-delete]').forEach(button => {
    button.addEventListener('click', function() {
        if (!confirm('Are you sure you want to delete this item?')) return;
        
        const id = this.dataset.id;
        const type = this.dataset.delete;
        
        fetch(`/facilities/admin/${type}/${id}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success || data.status === 'success') {
                showToast(`${type} deleted successfully`);
                location.reload();
            } else {
                showToast(data.message || `Error deleting ${type}`, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast(`Error deleting ${type}`, 'error');
        });
    });
});

// Initialize Select2
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Select2
    $('.select2').select2({
        theme: 'bootstrap-5',
        placeholder: 'Select items',
        allowClear: true
    });
    
    // Add reset handlers for add buttons
    ['facility', 'sport', 'offer'].forEach(type => {
        const addButton = document.querySelector(`[data-bs-target="#add${type}Modal"]`);
        if (addButton) {
            addButton.addEventListener('click', () => resetForm(`${type}Form`));
        }
    });
});