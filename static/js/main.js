document.addEventListener('DOMContentLoaded', function() {
    // Initialize booking functionality
    initializeBookingButtons();

    // Initialize AOS
    AOS.init({
        duration: 800,
        easing: 'ease-in-out',
        once: true
    });

    // Initialize all tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Weather Widget Update
    function updateWeather() {
        const weatherWidget = document.querySelector('.weather-widget');
        if (weatherWidget) {
            fetch('/bookings/api/weather/')
                .then(response => response.json())
                .then(data => {
                    weatherWidget.querySelector('.weather-icon').className = `weather-icon fas fa-${data.icon}`;
                    weatherWidget.querySelector('.temperature').textContent = `${data.temperature}°C`;
                    weatherWidget.querySelector('.conditions').textContent = data.conditions;
                    weatherWidget.querySelector('.humidity').textContent = `Humidity: ${data.humidity}%`;
                })
                .catch(error => console.error('Weather update failed:', error));
        }
    }

    // Live Activity Feed Update
    function updateActivityFeed() {
        const activityList = document.querySelector('.activity-list');
        if (activityList) {
            fetch('/bookings/api/activities/')
                .then(response => response.json())
                .then(data => {
                    const activities = data.map(activity => `
                        <div class="activity-item" data-aos="fade-left">
                            <div class="activity-icon">
                                <i class="fas fa-calendar-${activity.type.toLowerCase()}"></i>
                            </div>
                            <div class="activity-content">
                                <p>${activity.message}</p>
                                <small>${activity.timestamp} ago</small>
                            </div>
                        </div>
                    `).join('');
                    activityList.innerHTML = activities || '<p class="text-center">No recent activities</p>';
                })
                .catch(error => console.error('Activity feed update failed:', error));
        }
    }

    // Slot Booking System
    const bookingModal = document.getElementById('bookingModal');
    if (bookingModal) {
        bookingModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const slotId = button.getAttribute('data-slot-id');
            const slotTime = button.closest('.slot-card').querySelector('.slot-time').textContent;
            const date = document.querySelector('.date-btn.btn-primary').getAttribute('data-date');
            
            document.getElementById('slotIdInput').value = slotId;
            document.getElementById('bookingDate').textContent = date;
            document.getElementById('bookingTime').textContent = slotTime;

            // Update price based on selected sport
            const sportSelect = document.querySelector('select[name="sport_id"]');
            const updatePrice = () => {
                const option = sportSelect.selectedOptions[0];
                document.getElementById('bookingPrice').textContent = option.getAttribute('data-price');
            };
            sportSelect.addEventListener('change', updatePrice);
            updatePrice();
        });
    }

    // Handle offer selection in booking modal
    const offerSelect = document.querySelector('select[name="offer_id"]');
    if (offerSelect) {
        offerSelect.addEventListener('change', function() {
            const basePrice = parseFloat(document.getElementById('bookingPrice').textContent);
            const discountPercentage = this.selectedOptions[0].getAttribute('data-discount') || 0;
            const finalPrice = basePrice * (1 - discountPercentage / 100);
            document.getElementById('bookingPrice').textContent = finalPrice.toFixed(2);
        });
    }

    // Initialize periodic updates
    if (document.querySelector('.weather-widget')) {
        updateWeather();
        setInterval(updateWeather, 300000); // Update every 5 minutes
    }

    if (document.querySelector('.activity-list')) {
        updateActivityFeed();
        setInterval(updateActivityFeed, 60000); // Update every minute
    }



    // Add scroll animation for navbar
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('navbar-scrolled');
            } else {
                navbar.classList.remove('navbar-scrolled');
            }
        });
    }

    // Initialize Swipers
    // Hero Swiper
    new Swiper('.hero-swiper', {
        loop: true,
        autoplay: {
            delay: 5000,
        },
        pagination: {
            el: '.swiper-pagination',
            clickable: true,
        },
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },
    });

    // Offers Swiper
    new Swiper('.offers-swiper', {
        slidesPerView: 1,
        spaceBetween: 20,
        pagination: {
            el: '.swiper-pagination',
            clickable: true,
        },
        breakpoints: {
            640: {
                slidesPerView: 2,
            },
            1024: {
                slidesPerView: 3,
            },
        },
    });

    // Testimonials Swiper
    new Swiper('.testimonials-swiper', {
        slidesPerView: 1,
        spaceBetween: 30,
        pagination: {
            el: '.swiper-pagination',
            clickable: true,
        },
        breakpoints: {
            768: {
                slidesPerView: 2,
            },
            1024: {
                slidesPerView: 3,
            },
        },
    });

    // Function to initialize booking buttons and modal functionality
    function initializeBookingButtons() {
        const bookingModal = document.getElementById('bookingModal');
        if (!bookingModal) return;

        const modal = new bootstrap.Modal(bookingModal);
        const slotButtons = document.querySelectorAll('.book-btn');
        const facilitySelect = document.querySelector('select[name="facility_sport"]');
        const bookingSummary = document.querySelector('.booking-summary');
        const bookingForm = document.getElementById('bookingForm');

        // Handle slot selection
        slotButtons.forEach(button => {
            button.addEventListener('click', function() {
                const slotId = this.dataset.slotId;
                const slotTime = this.dataset.slotTime;
                
                document.getElementById('slotIdInput').value = slotId;
                document.getElementById('selectedTime').textContent = slotTime;
                document.getElementById('summaryTime').textContent = slotTime;

                // Format date nicely
                const today = new Date();
                const formattedDate = today.toLocaleDateString('en-US', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });
                document.getElementById('summaryDate').textContent = formattedDate;

                // Reset facility selection
                if (facilitySelect) {
                    facilitySelect.selectedIndex = 0;
                    bookingSummary.classList.add('d-none');
                }

                modal.show();
            });
        });

        // Handle facility selection
        if (facilitySelect) {
            facilitySelect.addEventListener('change', function() {
                const selected = this.selectedOptions[0];
                if (selected.value) {
                    const price = selected.dataset.price;
                    document.getElementById('summaryFacility').textContent = selected.text.split(' (₹')[0];
                    document.getElementById('summaryPrice').textContent = price;
                    document.getElementById('summaryFinalPrice').textContent = price;
                    bookingSummary.classList.remove('d-none');
                } else {
                    bookingSummary.classList.add('d-none');
                }
            });
        }

        // Handle form submission
        if (bookingForm) {
            bookingForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                if (facilitySelect && !facilitySelect.value) {
                    alert('Please select a facility and sport');
                    return;
                }

                const formData = new FormData(this);
                fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Booking failed');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.status === 'error') {
                        console.error('Booking error:', data.message);
                        alert('Error creating booking: ' + data.message);
                        return;
                    }
                    modal.hide();
                    alert('Booking created successfully!');
                    window.location.reload();
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error creating booking. Please try again.');
                });
            });
        }
    }

    // Image Preview for File Inputs
    const imageInputs = document.querySelectorAll('input[type="file"][accept^="image"]');
    imageInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const preview = document.getElementById(`${this.id}-preview`);
            if (preview && this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = e => preview.src = e.target.result;
                reader.readAsDataURL(this.files[0]);
            }
        });
    });
});