from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q
from django.template.defaultfilters import timesince
from facilities.models import FacilitySport, TimeSlot, Offer
from .models import Booking

@api_view(['GET'])
def get_activities(request):
    """Get recent booking activities"""
    recent_activities = []
    recent_bookings = Booking.objects.select_related(
        'user', 'facility_sport__facility'
    ).filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-created_at')[:10]

    for booking in recent_bookings:
        activity_type = booking.status.title()
        if booking.status == 'confirmed':
            color = '#28a745'
        elif booking.status == 'pending':
            color = '#ffc107'
        else:
            color = '#dc3545'
            
        recent_activities.append({
            'type': activity_type,
            'color': color,
            'timestamp': timesince(booking.created_at),
            'message': f"{booking.user.get_full_name() or booking.user.username} booked {booking.facility_sport.facility.name}"
        })
    
    return Response(recent_activities)

@api_view(['GET'])
def get_weather(request):
    """Get current weather data (placeholder)"""
    # This is a placeholder. In production, you'd integrate with a weather API
    return Response({
        'temperature': 28,
        'conditions': 'Sunny',
        'humidity': 65,
        'icon': 'sun'
    })

from datetime import datetime, timedelta
from .models import Booking, Review
from facilities.models import FacilitySport, Offer, TimeSlot

@api_view(['GET'])
def get_slots(request):
    """Get available slots for a given date and optional facility"""
    try:
        date_str = request.query_params.get('date')
        facility_id = request.query_params.get('facility_id')
        
        if not date_str:
            return Response({'error': 'Date parameter is required'}, status=400)
        
        # Parse date
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
        
        # Validate facility and get available sports
        if facility_id:
            facility_sports = FacilitySport.objects.filter(
                facility_id=facility_id,
                is_available=True
            ).select_related('sport', 'facility')
            
            if not facility_sports.exists():
                return Response({
                    'error': 'No sports available for this facility. Please contact the administrator.'
                }, status=404)
        else:
            return Response({'error': 'Facility ID is required'}, status=400)
        
        # Get current time for past slot checks
        now = timezone.localtime()
        is_today = selected_date == now.date()
        
        # Get all time slots
        time_slots = TimeSlot.objects.all().order_by('start_time')
        
        # Query existing bookings for this facility and date
        existing_bookings = Booking.objects.filter(
            facility_sport__facility_id=facility_id,
            date=selected_date,
            status__in=['confirmed', 'payment_pending']
        ).select_related('time_slot')
        
        booked_slots = {(b.time_slot_id, b.facility_sport_id) for b in existing_bookings}
        
        # Generate slots with availability for each sport
        slots = []
        for time_slot in time_slots:
            # Check if slot is in the past
            slot_start = datetime.combine(selected_date, time_slot.start_time)
            is_past = is_today and now.time() > time_slot.start_time
            
            # Format display time
            display_time = f"{time_slot.start_time.strftime('%I:%M %p')} - {time_slot.end_time.strftime('%I:%M %p')}"
            
            # Handle lunch break slot
            if time_slot.slot_time == '12:00-13:00':
                slots.append({
                    'id': f"lunch_{time_slot.id}",
                    'start_time': time_slot.start_time.strftime('%H:%M'),
                    'end_time': time_slot.end_time.strftime('%H:%M'),
                    'slot_time': time_slot.slot_time,
                    'display_time': display_time,
                    'is_past': is_past,
                    'is_lunch': True,
                    'is_available': False
                })
                continue
            
            # For each available sport in the facility
            for facility_sport in facility_sports:
                slot_id = f"{selected_date.strftime('%Y-%m-%d')}_{time_slot.id}_{facility_sport.id}"
                is_booked = (time_slot.id, facility_sport.id) in booked_slots
                
                slot = {
                    'id': slot_id,
                    'start_time': time_slot.start_time.strftime('%H:%M'),
                    'end_time': time_slot.end_time.strftime('%H:%M'),
                    'slot_time': time_slot.slot_time,
                    'display_time': display_time,
                    'sport_name': facility_sport.sport.name,
                    'price': float(facility_sport.price_per_slot),
                    'is_past': is_past,
                    'is_lunch': False,
                    'is_booked': is_booked,
                    'is_available': not is_past and not is_booked
                }
                slots.append(slot)
        
        # Get active offers
        offers = Offer.objects.filter(
            facility_id=facility_id,
            start_date__lte=selected_date,
            end_date__gte=selected_date,
            is_active=True
        ).values('title', 'discount_percentage')
        
        return Response({
            'slots': slots,
            'offers': offers
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)