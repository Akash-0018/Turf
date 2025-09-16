from django.db import models
from django.conf import settings
from facilities.models import Facility
from bookings.models import Booking

class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_reviews')
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='facility_reviews')
    booking = models.OneToOneField(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='booking_review')
    rating = models.IntegerField(choices=RATING_CHOICES)
    review_text = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['facility', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
        
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.facility.name} ({self.rating} stars)"

class Reply(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reply_text = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
        verbose_name_plural = 'Replies'
        
    def __str__(self):
        return f"Reply to {self.review} by {self.user.get_full_name()}"