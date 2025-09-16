from rest_framework import serializers
from .models import Payment
from bookings.serializers import BookingSerializer

class PaymentSerializer(serializers.ModelSerializer):
    booking_detail = BookingSerializer(source='booking', read_only=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'user', 'booking', 'booking_detail', 'amount', 
                 'payment_method', 'transaction_id', 'status', 'payment_date', 
                 'last_updated']
        read_only_fields = ['user', 'status', 'payment_date', 'last_updated']