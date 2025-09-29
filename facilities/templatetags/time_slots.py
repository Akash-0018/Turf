from django import template
from facilities.models import TimeSlot

register = template.Library()

@register.simple_tag
def get_time_slots():
    """Return all available time slots"""
    return TimeSlot.objects.all().order_by('start_time')