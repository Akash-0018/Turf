from django.shortcuts import render
from django.utils import timezone
from django.db.models import Avg
from facilities.models import Facility, FacilitySport, TimeSlot
from facilities.models import SportType, Offer
from bookings.models import Booking
from reviews.models import Review
import pytz

def home(request):
    # Get the featured facility with all related data
    facility = Facility.objects.prefetch_related(
        'images',
        'sports__sport',
        'offers'
    ).first()
    
    # Use IST timezone for all slot logic
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = timezone.now().astimezone(ist)
    today = now_ist.date()
    dates = [today + timezone.timedelta(days=x) for x in range(3)]

    # Get simulated weather data for Coimbatore based on seasonal patterns
    current_hour = now_ist.hour
    current_month = now_ist.month
    
    # Coimbatore's seasonal temperature ranges (°C)
    if current_month in [12, 1, 2]:  # Winter
        temp_range = (18, 30)
        humidity_range = (40, 65)
    elif current_month in [3, 4, 5]:  # Summer
        temp_range = (24, 35)
        humidity_range = (35, 55)
    elif current_month in [6, 7, 8, 9]:  # Monsoon
        temp_range = (22, 32)
        humidity_range = (70, 90)
    else:  # Post-monsoon
        temp_range = (20, 31)
        humidity_range = (60, 75)

    # Adjust temperature based on time of day
    if 6 <= current_hour < 12:  # Morning
        temperature = temp_range[0] + (temp_range[1] - temp_range[0]) * 0.4
    elif 12 <= current_hour < 16:  # Afternoon
        temperature = temp_range[1]
    elif 16 <= current_hour < 20:  # Evening
        temperature = temp_range[0] + (temp_range[1] - temp_range[0]) * 0.6
    else:  # Night
        temperature = temp_range[0]

    # Determine weather conditions based on month and time
    if current_month in [6, 7, 8, 9]:  # Monsoon months
        conditions = 'Cloudy' if 6 <= current_hour < 18 else 'Partly Cloudy'
        humidity = humidity_range[1]
    else:
        if 6 <= current_hour < 18:
            conditions = 'Sunny' if current_hour > 10 else 'Clear'
        else:
            conditions = 'Clear'
        humidity = humidity_range[0] + (humidity_range[1] - humidity_range[0]) * 0.5

    weather = {
        'temperature': int(temperature),
        'conditions': conditions,
        'humidity': int(humidity)
    }
    
    # Get slots for each date
    all_slots = TimeSlot.objects.all()
    date_slots = {}
    
    for date in dates:
        # Get booked slots for the date
        booked_slots = Booking.objects.filter(
            date=date,
            status__in=['confirmed', 'pending'],
        ).values_list('time_slot_id', flat=True)
        
        booked_slot_ids = set(booked_slots)
        
        # Get current time for checking past slots
        current_time = now_ist.time() if date == today else None
        # Filter available slots
        available_slots = []
        for slot in all_slots:
            # For today's slots, check if the slot's start time has passed
            is_past = False
            if date == today:
                current_hour = current_time.hour
                current_minute = current_time.minute
                slot_hour = slot.start_time.hour
                slot_minute = slot.start_time.minute
                
                # Convert both times to minutes for easier comparison
                current_minutes = current_hour * 60 + current_minute
                slot_minutes = slot_hour * 60 + slot_minute
                
                is_past = slot_minutes <= current_minutes
                
            is_available = slot.id not in booked_slot_ids and not is_past
            slot_data = {
                'id': slot.id,
                'slot_time': slot.slot_time,
                'display_time': slot.get_slot_time_display(),
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'is_available': is_available,
                'is_past': is_past
            }
            available_slots.append(slot_data)
        
        date_slots[date] = available_slots
    
    # Get available sports with prices
    facility_sports = FacilitySport.objects.filter(facility=facility, is_available=True).select_related('sport')
    
    # Get active offers
    offers = Offer.objects.filter(
        facility=facility,
        start_date__lte=today,
        end_date__gte=today,
        is_active=True
    )
    
    # Get time slots for today
    slots = TimeSlot.objects.all().order_by('start_time')
    
    # Weather data is already set from API call above
    
    # Mock activities (replace with actual data)
    activities = [
        {
            'message': 'New booking confirmed',
            'timestamp': timezone.now() - timezone.timedelta(minutes=30),
            'get_icon': 'fa-check-circle',
        },
        {
            'message': 'Field maintenance completed',
            'timestamp': timezone.now() - timezone.timedelta(hours=1),
            'get_icon': 'fa-tools',
        },
    ]
    
    # Get approved featured reviews
    featured_reviews = Review.objects.filter(
        is_approved=True,
        is_featured=True,
        facility=facility
    ).select_related('user').order_by('-created_at')[:6]
    
    # Get facility rating
    facility_rating = Review.objects.filter(
        facility=facility,
        is_approved=True
    ).aggregate(avg_rating=Avg('rating'))
    
    context = {
        'turf': facility,
        'dates': dates,
        'date_slots': date_slots,
        'turf_sports': facility_sports,
        'offers': offers,
        'weather': weather,
        'activities': activities,
        'slots': slots,
        'selected_date': today,
        'featured_reviews': featured_reviews,
        'facility_rating': facility_rating['avg_rating'] or 0
    }
    return render(request, 'home.html', context)

def about_us(request):
    return render(request, 'pages/about.html')

def contact_us(request):
    return render(request, 'pages/contact.html')

def privacy_policy(request):
    return render(request, 'pages/privacy.html')

def terms_conditions(request):
    return render(request, 'pages/terms.html')

def faq(request):
    return render(request, 'pages/faq.html')

def careers(request):
    return render(request, 'pages/careers.html')