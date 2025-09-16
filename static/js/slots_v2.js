// Format time for display (HH:MM format to 12-hour format)
function formatTime(time) {
    const [hours, minutes] = time.split(':');
    const date = new Date();
    date.setHours(hours);
    date.setMinutes(minutes);
    return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
    });
}

// Function to format a slot for display
function formatSlot(slot) {
    let statusClass = '';
    let statusText = '';
    let statusIcon = '';
    
    DEBUG.debug('Formatting slot', slot);
    
    if (slot.is_past) {
        statusClass = 'status-past';
        statusText = 'Past';
        statusIcon = 'fa-clock';
    } else if (slot.is_lunch) {
        statusClass = 'status-lunch';
        statusText = 'Lunch Break';
        statusIcon = 'fa-utensils';
    } else if (slot.is_booked) {
        statusClass = 'status-booked';
        statusText = 'Booked';
        statusIcon = 'fa-lock';
    } else if (slot.is_available) {
        statusClass = 'status-available';
        statusText = 'Available';
        statusIcon = 'fa-check-circle';
    }

    // Format display time if not provided
    let displayTime = slot.display_time;
    if (!displayTime && slot.start_time && slot.end_time) {
        displayTime = `${formatTime(slot.start_time)} - ${formatTime(slot.end_time)}`;
    }
    
    let sportDisplay = slot.sport_name ? `<div class="slot-sport">${slot.sport_name}</div>` : '';
    let priceDisplay = slot.price ? `<div class="slot-price">₹${slot.price.toFixed(2)}</div>` : '';
    
    let html = `
        <div class="slot-card ${slot.is_past ? 'past' : ''}" data-slot-id="${slot.id}">
            <div class="slot-time">
                <i class="far fa-clock"></i>
                ${displayTime}
            </div>
            ${sportDisplay}
            ${priceDisplay}
            <div class="slot-status ${statusClass}">
                <i class="fas ${statusIcon}"></i>
                <span class="status-label">${statusText}</span>
            </div>`;
            
    if (!slot.is_past && !slot.is_lunch && slot.is_available) {
        const bookingData = {
            id: slot.id,
            display_time: displayTime,
            start_time: slot.start_time,
            end_time: slot.end_time,
            sport_name: slot.sport_name,
            price: slot.price
        };

        html += `
            <button class="book-now-btn" 
                    data-booking='${JSON.stringify(bookingData)}'
                    data-bs-toggle="modal"
                    data-bs-target="#bookingModal"
                    onclick="openBookingModal(this)">
                <i class="fas fa-calendar-check"></i>
                Book Now (₹${slot.price.toFixed(2)})
            </button>`;
    }
    
    html += '</div>';
    return html;
}

// Function to load slots for a date
function loadSlots(date, facilityId = null) {
    const slotsContainer = document.querySelector('#slots-container');
    if (!slotsContainer) {
        DEBUG.warn('Slots container not found');
        return;
    }
    
    // Add loading state
    slotsContainer.classList.add('loading');
    trackUiUpdate(slotsContainer, 'add-loading');
    
    let url = '/bookings/get-slots/';
    const params = new URLSearchParams();
    params.append('date', date);
    
    // Get facility ID from parameter or select element
    const selectedFacility = facilityId || document.querySelector('select[name="facility"]')?.value;
    DEBUG.info('Loading slots with parameters:', { date, facilityId: selectedFacility });
    if (selectedFacility) {
        params.append('facility_id', selectedFacility);
        DEBUG.info('Loading slots for facility', { facilityId: selectedFacility, date });
    } else {
        DEBUG.warn('No facility ID provided');
    }
    
    url += '?' + params.toString();
    const apiTracker = trackApiCall(url, 'GET');
    
    fetch(url)
        .then(response => {
            DEBUG.info('Slots API response', { 
                status: response.status, 
                ok: response.ok,
                headers: Object.fromEntries(response.headers)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Remove loading state
            slotsContainer.classList.remove('loading');
            trackUiUpdate(slotsContainer, 'remove-loading');
            apiTracker.end();
            
            DEBUG.debug('Slots data received', data);
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            if (!Array.isArray(data.slots)) {
                DEBUG.error('Invalid slots data format', data);
                throw new Error('Invalid data format received from server');
            }
            
            if (data.slots.length === 0) {
                DEBUG.info('No slots available', { date, facilityId: selectedFacility });
                slotsContainer.innerHTML = `
                    <div class="text-center p-5">
                        <i class="fas fa-calendar-times fa-2x"></i>
                        <p class="mt-3">No slots available for this date</p>
                    </div>`;
                return;
            }
            
            DEBUG.info(`Processing ${data.slots.length} slots`);
            const slotsHtml = data.slots.map(slot => {
                trackSlotOperation('format', slot);
                return formatSlot(slot);
            }).join('');
            slotsContainer.innerHTML = slotsHtml;
            
            // Update offers if available
            const offersContainer = document.querySelector('.offers-container');
            if (offersContainer && Array.isArray(data.offers)) {
                offersContainer.innerHTML = data.offers.length > 0 
                    ? data.offers.map(offer => `
                        <div class="offer-badge">
                            <i class="fas fa-tag"></i>
                            ${offer.title} - ${offer.discount_percentage}% off
                        </div>
                    `).join('')
                    : '<p>No active offers</p>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            slotsContainer.classList.remove('loading');
            slotsContainer.innerHTML = `
                <div class="text-center p-5">
                    <i class="fas fa-exclamation-triangle fa-2x text-danger"></i>
                    <p class="mt-3">${error.message || 'Error loading slots. Please try again.'}</p>
                </div>`;
        });
}

// Function to handle booking modal
function openBookingModal(buttonElement) {
    try {
        DEBUG.info('Opening booking modal');
        
        if (!buttonElement || !buttonElement.dataset.booking) {
            DEBUG.error('Invalid button element or missing booking data');
            throw new Error('Invalid booking data');
        }
        
        const bookingData = JSON.parse(buttonElement.dataset.booking);
        DEBUG.debug('Parsed booking data', bookingData);
        
        const modal = document.getElementById('bookingModal');
        if (!modal) {
            DEBUG.error('Booking modal element not found');
            throw new Error('Booking modal not found');
        }
        
        trackUiUpdate(modal, 'prepare-modal');
        
        // Update modal content with slot details
        const timeDisplay = modal.querySelector('.booking-time');
        if (timeDisplay) {
            timeDisplay.textContent = `${bookingData.sport_name} - ${bookingData.display_time}`;
            trackUiUpdate(timeDisplay, 'update-time');
        } else {
            DEBUG.warn('Time display element not found in modal');
        }
        
        const priceDisplay = modal.querySelector('.booking-price');
        if (priceDisplay) {
            priceDisplay.textContent = `₹${bookingData.price.toFixed(2)}`;
            trackUiUpdate(priceDisplay, 'update-price');
        } else {
            DEBUG.warn('Price display element not found in modal');
        }
        
        // Store booking data for later use
        modal.dataset.booking = JSON.stringify(bookingData);
        DEBUG.info('Modal prepared successfully', {
            sport: bookingData.sport_name,
            time: bookingData.display_time,
            price: bookingData.price
        });
    } catch (error) {
        trackError('openBookingModal', error);
        alert('Sorry, there was an error opening the booking form. Please try again.');
    }
}

// Function to confirm booking
function confirmBooking(modalElement) {
    DEBUG.info('Starting booking confirmation');
    
    let bookingData;
    try {
        bookingData = JSON.parse(modalElement.dataset.booking || '{}');
        DEBUG.debug('Parsed booking data', bookingData);
    } catch (error) {
        trackError('confirmBooking - parsing', error);
        return;
    }
    
    const slotId = bookingData.id;
    if (!slotId) {
        DEBUG.error('No slot ID found in booking data');
        return;
    }
    
    // Show loading state
    const submitButton = modalElement.querySelector('button[type="submit"]');
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        trackUiUpdate(submitButton, 'disable-submit');
    } else {
        DEBUG.warn('Submit button not found');
    }
    
    const facilityId = document.querySelector('select[name="facility"]')?.value;
    if (!facilityId) {
        DEBUG.warn('No facility ID found');
    }
    
    const requestData = {
        slot_id: slotId,
        facility_id: facilityId
    };
    
    // Make booking API call
    DEBUG.info('Making booking API call', requestData);
    const apiTracker = trackApiCall('/bookings/api/book/', 'POST', requestData);
    
    fetch('/bookings/api/book/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        DEBUG.info('Booking API response', {
            status: response.status,
            ok: response.ok,
            headers: Object.fromEntries(response.headers)
        });
        return response.json();
    })
    .then(data => {
        apiTracker.end();
        DEBUG.debug('Booking response data', data);
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Close modal and show success message
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
            trackUiUpdate(modalElement, 'hide-modal');
        } else {
            DEBUG.warn('Modal instance not found');
        }
        
        // Show success toast or message
        showNotification('success', 'Booking confirmed successfully!');
        
        // Reload slots to reflect changes
        const dateInput = document.querySelector('input[name="selected_date"]');
        if (dateInput) {
            DEBUG.info('Reloading slots after successful booking');
            loadSlots(dateInput.value);
        } else {
            DEBUG.warn('Date input not found for slot reload');
        }
    })
    .catch(error => {
        trackError('confirmBooking - API', error);
        showNotification('error', error.message || 'Error making booking. Please try again.');
    })
    .finally(() => {
        // Reset button state
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = 'Confirm Booking';
            trackUiUpdate(submitButton, 'enable-submit');
        }
    });
}

// Helper function to get CSRF token
function getCsrfToken() {
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return csrfInput ? csrfInput.value : '';
}

// Helper function to show notifications
function showNotification(type, message) {
    // You can implement this based on your UI library or custom toast/alert system
    if (type === 'error') {
        alert(message); // Fallback to alert for now
    } else {
        alert(message);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Set default date to today
    const datePicker = document.querySelector('input[name="selected_date"]');
    if (datePicker) {
        const today = new Date().toISOString().split('T')[0];
        datePicker.value = today;
        datePicker.min = today; // Can't select past dates
    }
    
    // Load slots for default facility if any
    const facilitySelect = document.querySelector('select[name="facility"]');
    if (facilitySelect) {
        const facilityId = facilitySelect.value;
        if (facilityId) {
            loadSlots(datePicker?.value || new Date().toISOString().split('T')[0], facilityId);
        }
    }
});