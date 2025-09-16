from rest_framework import serializers
from django.db import models
from .models import Booking
from facilities.serializers import FacilitySerializer

class BookingSerializer(serializers.ModelSerializer):
    facility_detail = FacilitySerializer(source='facility', read_only=True)
    
    class Meta:
        model = Booking
        fields = ['id', 'user', 'facility', 'facility_detail', 'booking_type', 
                 'team_size', 'date', 'start_time', 'end_time', 'status', 
                 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['user', 'status', 'total_price']
        
    def validate(self, data):
        """
        Check that the booking times are valid and facility is available
        """
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("End time must be after start time")
            
        # Check for booking conflicts
        conflicts = Booking.objects.filter(
            facility=data['facility'],
            date=data['date'],
            status='confirmed'
        ).exclude(
            id=self.instance.id if self.instance else None
        ).filter(
            models.Q(start_time__lt=data['end_time']) & 
            models.Q(end_time__gt=data['start_time'])
        )
        
        if conflicts.exists():
            raise serializers.ValidationError("This time slot is already booked")
            
        return data