from django.db import models
from django.conf import settings
from django.utils import timezone
from facilities.models import Facility, FacilitySport, TimeSlot, Offer
from datetime import datetime
import pytz

class Booking(models.Model):
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),    # New status for just created bookings
        ('payment_pending', 'Payment Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('expired', 'Expired')         # For bookings that weren't paid in time
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    facility_sport = models.ForeignKey(FacilitySport, on_delete=models.CASCADE, related_name='bookings', null=True)
    date = models.DateField()
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='bookings', null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Total price after discounts
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Original price before discounts
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Amount of discount applied
    discount_code = models.CharField(max_length=50, blank=True, null=True)  # For tracking which offer was applied
    payment_deadline = models.DateTimeField(null=True)  # When the booking expires if not paid
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        unique_together = ['facility_sport', 'date', 'time_slot']  # Prevent double bookings

    def __str__(self):
        return f"{self.user.username} - {self.facility_sport.facility.name} - {self.facility_sport.sport.name} ({self.date})"

    def save(self, *args, **kwargs):
        # Ensure facility_sport and time_slot are provided for new bookings
        if not self.id and (not self.facility_sport or not self.time_slot):
            raise ValueError("Both facility_sport and time_slot are required for new bookings")

        # Set payment deadline for new bookings (30 minutes from creation)
        if not self.id and not self.payment_deadline:
            self.payment_deadline = timezone.now() + timezone.timedelta(minutes=30)

        # Calculate prices if this is a new booking
        if not self.id and not self.base_price:
            self.base_price = self.facility_sport.price_per_slot
            self.total_price = self.base_price
            
            # Apply active offers only to eligible slots
            active_offer = Offer.objects.filter(
                facility=self.facility_sport.facility,
                start_date__lte=self.date,
                end_date__gte=self.date,
                is_active=True
            ).first()
            
            if active_offer:
                # Early bird offer logic - only for slots between 6 AM and 10 AM IST
                slot_time = timezone.localtime(timezone.make_aware(datetime.combine(self.date, self.time_slot.start_time)))
                slot_hour = slot_time.hour
                if 6 <= slot_hour < 10:  # Early bird hours (6 AM to 10 AM IST)
                    self.discount_amount = self.base_price * (active_offer.discount_percentage / 100)
                    self.total_price = self.base_price - self.discount_amount
                    self.discount_code = f"EARLY_BIRD_{active_offer.id}"
        
        super().save(*args, **kwargs)

class LiveActivity(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='activity')
    action = models.CharField(max_length=50)  # e.g., "New Booking", "Booking Approved", etc.
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Live Activities'
