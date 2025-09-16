from django.db import models
from django.conf import settings

class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default='TurfZone')
    logo = models.ImageField(upload_to='site/', null=True, blank=True)
    favicon = models.ImageField(upload_to='site/', null=True, blank=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    about_us = models.TextField()
    booking_time_limit = models.IntegerField(default=15)  # minutes
    cancellation_time_limit = models.IntegerField(default=24)  # hours
    max_advance_booking_days = models.IntegerField(default=30)
    maintenance_mode = models.BooleanField(default=False)
    terms_conditions = models.TextField(blank=True)
    privacy_policy = models.TextField(blank=True)
    social_links = models.JSONField(default=dict)
    
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
    
    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            return  # Prevent creating multiple settings instances
        return super().save(*args, **kwargs)

class Facility(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    amenities = models.JSONField(default=list)
    rules = models.TextField(blank=True)
    opening_time = models.TimeField(default='06:00')
    closing_time = models.TimeField(default='23:00')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Facility'
        verbose_name_plural = 'Facilities'

    def __str__(self):
        return self.name

class FacilityImage(models.Model):
    facility = models.ForeignKey(Facility, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='facility_images/')
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']

class SportType(models.Model):
    name = models.CharField(max_length=50)
    icon = models.ImageField(upload_to='sport_icons/', null=True, blank=True)
    
    def __str__(self):
        return self.name

class FacilitySport(models.Model):
    facility = models.ForeignKey(Facility, related_name='sports', on_delete=models.CASCADE)
    sport = models.ForeignKey(SportType, on_delete=models.CASCADE)
    price_per_slot = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('facility', 'sport')

class Offer(models.Model):
    facility = models.ForeignKey(Facility, related_name='offers', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.title} - {self.discount_percentage}% off"

class TimeSlot(models.Model):
    SLOT_CHOICES = [
        ('06:00-08:00', '6 AM - 8 AM'),
        ('08:00-10:00', '8 AM - 10 AM'),
        ('10:00-12:00', '10 AM - 12 PM'),
        ('12:00-13:00', 'Lunch Break'),
        ('14:00-16:00', '2 PM - 4 PM'),
        ('16:00-18:00', '4 PM - 6 PM'),
        ('18:00-20:00', '6 PM - 8 PM'),
        ('20:00-22:00', '8 PM - 10 PM'),
        ('22:00-00:00', '10 PM - 12 AM'),
    ]
    
    slot_time = models.CharField(max_length=20, choices=SLOT_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    def __str__(self):
        return self.get_slot_time_display()
