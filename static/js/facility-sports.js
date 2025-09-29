// Handle facility sports management
document.querySelectorAll('.manage-sports').forEach(btn => {
    btn.addEventListener('click', function() {
        const facilityId = this.dataset.id;
        loadFacilitySports(facilityId);
    });
});

function loadFacilitySports(facilityId) {
    fetch(`/facilities/admin/facility/${facilityId}/sports/`)
        .then(response => response.json())
        .then(data => {
            const currentSportsList = document.getElementById('currentSportsList');
            const sportSelect = document.getElementById('sportSelect');
            const form = document.getElementById('facilitySportsForm');
            
            // Set facility ID for form submission
            form.dataset.facilityId = facilityId;
            
            // Update facility name in modal title
            document.querySelector('#manageSportsModal .modal-title').textContent = 
                `Manage Sports for ${data.facility_name}`;
            
            // Clear and populate current sports list
            currentSportsList.innerHTML = '';
            data.sports.forEach(sport => {
                currentSportsList.innerHTML += `
                    <div class="list-group-item d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-0">${sport.name}</h6>
                            <small>₹${sport.price_per_slot}/slot - Max ${sport.max_players} players</small>
                        </div>
                        <div class="form-check form-switch">
                            <input class="form-check-input sport-availability" type="checkbox" 
                                   ${sport.is_available ? 'checked' : ''} 
                                   data-sport-id="${sport.id}">
                            <label class="form-check-label">Available</label>
                        </div>
                    </div>
                `;
            });
            
            // Clear and populate available sports dropdown
            sportSelect.innerHTML = '<option value="">Select a sport</option>';
            data.available_sports.forEach(sport => {
                sportSelect.innerHTML += `
                    <option value="${sport.id}">${sport.name}</option>
                `;
            });

            // Initialize or reinitialize Select2 for sport selection
            if ($('#sportSelect').hasClass('select2-hidden-accessible')) {
                $('#sportSelect').select2('destroy');
            }
            $('#sportSelect').select2({
                theme: 'bootstrap-5',
                dropdownParent: $('#manageSportsModal'),
                placeholder: 'Select a sport',
                allowClear: true,
                width: '100%'
            });
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error loading facility sports', 'error');
        });
}

// Handle saving facility sports
document.querySelector('.save-facility-sports').addEventListener('click', function() {
    const form = document.getElementById('facilitySportsForm');
    const facilityId = form.dataset.facilityId;
    const formData = new FormData(form);
    
    // Validate the form
    const sport = formData.get('sport');
    const pricePerSlot = formData.get('price_per_slot');
    const maxPlayers = formData.get('max_players');
    
    if (!sport) {
        showToast('Please select a sport', 'error');
        return;
    }
    
    if (!pricePerSlot || parseFloat(pricePerSlot) <= 0) {
        showToast('Please enter a valid price per slot', 'error');
        return;
    }
    
    if (!maxPlayers || parseInt(maxPlayers) < 1) {
        showToast('Please enter a valid number of maximum players', 'error');
        return;
    }
    
    fetch(`/facilities/admin/facility/${facilityId}/sports/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || 'Sports updated successfully', 'success');
            $('#manageSportsModal').modal('hide');
            // Reload the facility sports list
            loadFacilitySports(facilityId);
            // Clear the form
            form.reset();
            $('#sportSelect').val(null).trigger('change');
        } else {
            const errorMessage = data.errors && Object.values(data.errors).flat().join('\n') || data.message || 'Error updating sports';
            showToast(errorMessage, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error updating sports', 'error');
    });
});