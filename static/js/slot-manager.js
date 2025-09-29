class SlotManager {
    constructor(config = {}) {
        this.config = {
            slotsContainer: '#slotsContainer',
            dateSelector: '#date',
            facilitySelector: '#facilitySelect',
            sportSelector: '#sportSelect',
            loadingSpinner: '#loadingSpinner',
            noSlotsMessage: '#noSlotsMessage',
            slotCardTemplate: '#slotCardTemplate',
            offerBadgeTemplate: '#offerBadgeTemplate',
            ...config
        };
        
        this.slots = [];
        this.offers = [];
        this.selectedSlot = null;
        this.selectedFacilitySportId = null;
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Date change listener
        const dateInput = document.querySelector(this.config.dateSelector);
        if (dateInput) {
            dateInput.addEventListener('change', () => this.loadSlots());
        }

        // Facility change listener
        const facilitySelect = document.querySelector(this.config.facilitySelector);
        if (facilitySelect) {
            facilitySelect.addEventListener('change', () => {
                this.loadSlots();
                this.updateSportOptions();
            });
        }

        // Sport change listener
        const sportSelect = document.querySelector(this.config.sportSelector);
        if (sportSelect) {
            sportSelect.addEventListener('change', () => this.loadSlots());
        }
    }

    async loadSlots() {
        const dateInput = document.querySelector(this.config.dateSelector);
        const facilitySelect = document.querySelector(this.config.facilitySelector);
        const container = document.querySelector(this.config.slotsContainer);
        const loadingSpinner = document.querySelector(this.config.loadingSpinner);
        const noSlotsMessage = document.querySelector(this.config.noSlotsMessage);

        if (!dateInput?.value || !facilitySelect?.value) return;

        try {
            // Show loading state
            if (container) container.style.opacity = '0.5';
            if (loadingSpinner) loadingSpinner.classList.remove('d-none');
            if (noSlotsMessage) noSlotsMessage.classList.add('d-none');

            const response = await fetch(
                `/bookings/get-slots/?date=${dateInput.value}&facility_id=${facilitySelect.value}`,
                { headers: { 'X-Requested-With': 'XMLHttpRequest' } }
            );

            if (!response.ok) throw new Error('Failed to load slots');

            const data = await response.json();
            this.slots = data.slots;
            this.offers = data.offers;

            this.renderSlots();

        } catch (error) {
            console.error('Error loading slots:', error);
            this.showError('Failed to load available slots. Please try again.');
        } finally {
            if (container) container.style.opacity = '1';
            if (loadingSpinner) loadingSpinner.classList.add('d-none');
        }
    }

    updateSportOptions() {
        const facilitySelect = document.querySelector(this.config.facilitySelector);
        const sportSelect = document.querySelector(this.config.sportSelector);
        
        if (!facilitySelect || !sportSelect) return;

        const selectedFacility = facilitySelect.options[facilitySelect.selectedIndex];
        const availableSports = selectedFacility.dataset.sports;

        if (availableSports) {
            const sports = JSON.parse(availableSports);
            sportSelect.innerHTML = '<option value="">Select Sport</option>';
            sports.forEach(sport => {
                const option = document.createElement('option');
                option.value = sport.id;
                option.textContent = sport.name;
                sportSelect.appendChild(option);
            });
            sportSelect.disabled = false;
        } else {
            sportSelect.innerHTML = '<option value="">No sports available</option>';
            sportSelect.disabled = true;
        }
    }

    renderSlots() {
        const container = document.querySelector(this.config.slotsContainer);
        const noSlotsMessage = document.querySelector(this.config.noSlotsMessage);
        const slotTemplate = document.querySelector(this.config.slotCardTemplate);
        const offerTemplate = document.querySelector(this.config.offerBadgeTemplate);
        
        if (!container || !slotTemplate) return;

        // Clear existing slots
        container.innerHTML = '';

        // Filter and sort slots
        const availableSlots = this.slots
            .filter(slot => !slot.is_past && !slot.is_lunch)
            .sort((a, b) => {
                return new Date('1970/01/01 ' + a.start_time) - new Date('1970/01/01 ' + b.start_time);
            });

        if (availableSlots.length === 0) {
            if (noSlotsMessage) noSlotsMessage.classList.remove('d-none');
            return;
        }

        // Group slots by time
        const slotGroups = this.groupSlotsByTime(availableSlots);

        // Render slot groups
        Object.entries(slotGroups).forEach(([time, slots]) => {
            const timeGroup = document.createElement('div');
            timeGroup.className = 'slot-time-group mb-4';
            
            // Add time header
            const timeHeader = document.createElement('h6');
            timeHeader.className = 'slot-time-header mb-3';
            timeHeader.textContent = time;
            timeGroup.appendChild(timeHeader);

            // Add slots grid
            const slotsGrid = document.createElement('div');
            slotsGrid.className = 'row g-3';

            slots.forEach(slot => {
                const slotCard = slotTemplate.content.cloneNode(true);
                
                // Update slot card content
                const card = slotCard.querySelector('.slot-card');
                card.dataset.slotId = slot.id;
                card.dataset.facilitySportId = slot.facility_sport_id;
                
                if (!slot.is_available) {
                    card.classList.add('unavailable');
                }

                // Update prices
                const basePrice = slotCard.querySelector('.base-price');
                if (basePrice) basePrice.textContent = `₹${slot.base_price}`;

                const currentPrice = slotCard.querySelector('.current-price');
                if (currentPrice) {
                    if (slot.discount_percentage > 0) {
                        currentPrice.textContent = `₹${slot.discounted_price}`;
                    } else {
                        currentPrice.textContent = `₹${slot.base_price}`;
                    }
                }

                // Add discount badge if applicable
                if (slot.discount_percentage > 0 && offerTemplate) {
                    const badge = offerTemplate.content.cloneNode(true);
                    const badgeText = badge.querySelector('.discount-text');
                    if (badgeText) {
                        badgeText.textContent = `${slot.discount_percentage}% OFF`;
                    }
                    card.querySelector('.slot-header')?.appendChild(badge);
                }

                // Update sport and timing info
                const sportName = slotCard.querySelector('.sport-name');
                if (sportName) sportName.textContent = slot.sport_name;

                const slotTime = slotCard.querySelector('.slot-time');
                if (slotTime) slotTime.textContent = slot.display_time;

                // Add status indicators
                if (slot.is_booked) {
                    card.classList.add('booked');
                    const statusBadge = card.querySelector('.status-badge');
                    if (statusBadge) {
                        statusBadge.textContent = 'Booked';
                        statusBadge.classList.add('bg-danger');
                    }
                }

                // Add click handler for available slots
                if (slot.is_available) {
                    card.addEventListener('click', () => this.handleSlotSelection(card, slot));
                }

                slotsGrid.appendChild(slotCard);
            });

            timeGroup.appendChild(slotsGrid);
            container.appendChild(timeGroup);
        });

        // Show any active offers
        this.renderOffers();
    }

    groupSlotsByTime(slots) {
        return slots.reduce((groups, slot) => {
            // Get time block (morning, afternoon, evening)
            const hour = parseInt(slot.start_time.split(':')[0]);
            let timeBlock = 'Morning (6 AM - 12 PM)';
            if (hour >= 12 && hour < 17) {
                timeBlock = 'Afternoon (12 PM - 5 PM)';
            } else if (hour >= 17) {
                timeBlock = 'Evening (5 PM - 10 PM)';
            }

            if (!groups[timeBlock]) {
                groups[timeBlock] = [];
            }
            groups[timeBlock].push(slot);
            return groups;
        }, {});
    }

    renderOffers() {
        const container = document.querySelector('.offers-container');
        if (!container || !this.offers.length) return;

        container.innerHTML = this.offers.map(offer => `
            <div class="alert alert-info">
                <i class="fas fa-tag me-2"></i>
                <strong>${offer.title}:</strong> Get ${offer.discount_percentage}% off on early morning slots!
            </div>
        `).join('');
    }

    handleSlotSelection(cardElement, slotData) {
        // Remove selection from previously selected slot
        document.querySelectorAll('.slot-card.selected').forEach(card => {
            if (card !== cardElement) {
                card.classList.remove('selected');
            }
        });

        // Toggle selection on clicked slot
        cardElement.classList.toggle('selected');

        // Update selected slot data
        if (cardElement.classList.contains('selected')) {
            this.selectedSlot = slotData;
            this.selectedFacilitySportId = slotData.facility_sport_id;
        } else {
            this.selectedSlot = null;
            this.selectedFacilitySportId = null;
        }

        // Update hidden form fields if they exist
        const timeSlotInput = document.querySelector('input[name="time_slot"]');
        const facilitySportInput = document.querySelector('input[name="facility_sport"]');
        
        if (timeSlotInput) {
            timeSlotInput.value = this.selectedSlot ? this.selectedSlot.id : '';
        }
        
        if (facilitySportInput) {
            facilitySportInput.value = this.selectedFacilitySportId || '';
        }

        // Trigger custom event for slot selection
        const event = new CustomEvent('slotSelected', {
            detail: {
                slot: this.selectedSlot,
                facilitySportId: this.selectedFacilitySportId
            }
        });
        document.dispatchEvent(event);
    }

    showError(message) {
        // Implement error display logic
        console.error(message);
        // You could show a toast notification or alert here
    }

    // Getters for selected data
    getSelectedSlot() {
        return this.selectedSlot;
    }

    getSelectedFacilitySportId() {
        return this.selectedFacilitySportId;
    }
}

// Export for use in other files
window.SlotManager = SlotManager;