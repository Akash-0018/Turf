from django.db import models
from django.conf import settings
from django.utils import timezone
from bookings.models import Booking

class PaymentSettings(models.Model):
    qr_code = models.ImageField(upload_to='payment_qr/', help_text="QR code image for payments")
    upi_id = models.CharField(max_length=255, help_text="UPI ID for direct payments")
    merchant_name = models.CharField(max_length=255, help_text="Merchant name for UPI payments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Payment Setting'
        verbose_name_plural = 'Payment Settings'

    def __str__(self):
        return f"Payment Settings - {self.merchant_name}"

    def save(self, *args, **kwargs):
        if self.is_active:
            # Set all other settings to inactive
            PaymentSettings.objects.exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('initiated', 'Initiated'),     # Payment just created
        ('processing', 'Processing'),   # Payment being processed
        ('completed', 'Completed'),     # Payment successful
        ('failed', 'Failed'),          # Payment failed
        ('refunded', 'Refunded'),      # Payment refunded
        ('expired', 'Expired')         # Payment window expired
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('qr', 'QR Code'),
        ('upi', 'UPI Direct'),
        ('gpay', 'Google Pay'),
        ('phonepe', 'PhonePe'),
        ('paytm', 'Paytm'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, unique=True)
    reference_id = models.CharField(max_length=100, blank=True, null=True)  # External payment reference
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='initiated')
    payment_date = models.DateTimeField(auto_now_add=True)
    completion_date = models.DateTimeField(null=True)  # When payment was completed/failed
    last_updated = models.DateTimeField(auto_now=True)
    failure_reason = models.TextField(blank=True)  # Store reason if payment fails
    metadata = models.JSONField(default=dict)  # Store additional payment info
    
    class Meta:
        ordering = ['-payment_date']
        
    def save(self, *args, **kwargs):
        # Set completion date when status changes to completed/failed
        if self.status in ['completed', 'failed'] and not self.completion_date:
            self.completion_date = timezone.now()
        
        # Update booking status based on payment status
        if self.booking and not kwargs.get('skip_booking_update', False):
            if self.status == 'completed':
                self.booking.status = 'confirmed'
            elif self.status == 'failed':
                self.booking.status = 'payment_pending'
            elif self.status == 'expired':
                self.booking.status = 'expired'
            elif self.status == 'refunded':
                self.booking.status = 'cancelled'
            self.booking.save()
        
        # Remove skip_booking_update if present
        if 'skip_booking_update' in kwargs:
            del kwargs['skip_booking_update']
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.booking.user.username} - ₹{self.amount} ({self.status})"
