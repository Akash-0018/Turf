from django.http import JsonResponse
from django.utils import timezone
from .models import Facility, TimeSlot
from bookings.models import Booking

def get_available_slots(request):
    """Get available time slots for a facility on a specific date."""
    try:
        facility_id = request.GET.get('facility_id')
        date_str = request.GET.get('date')

        if not facility_id or not date_str:
            return JsonResponse({'error': 'Facility ID and date are required'}, status=400)

        # Get facility
        try:
            facility = Facility.objects.get(id=facility_id)
        except Facility.DoesNotExist:
            return JsonResponse({'error': 'Facility not found'}, status=404)

        # Parse date
        try:
            date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)

        # Get booked slots for the date
        booked_slots = Booking.objects.filter(
            facility=facility,
            date=date,
            status__in=['pending', 'confirmed']
        ).values_list('time_slot_id', flat=True)

        # Get all time slots and check availability
        slots = []
        for slot in TimeSlot.objects.all().order_by('start_time'):
            is_available = slot.id not in booked_slots
            slots.append({
                'id': slot.id,
                'display_time': f'{slot.start_time.strftime("%I:%M %p")} - {slot.end_time.strftime("%I:%M %p")}',
                'is_available': is_available
            })

        return JsonResponse({'slots': slots})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)