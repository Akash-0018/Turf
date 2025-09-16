from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from facilities.models import (
    Facility,
    FacilityImage,
    SportType,
    FacilitySport,
    TimeSlot,
    Offer
)
import requests
from datetime import time, timedelta

class Command(BaseCommand):
    help = 'Sets up a sample facility with images and related data'

    def handle(self, *args, **kwargs):
        # Create facility if none exists
        facility, created = Facility.objects.get_or_create(
            name="TurfZone Arena Mumbai Central",
            defaults={
                'description': "Premium sports facility in Mumbai Central featuring state-of-the-art artificial turf, floodlights, and modern amenities. Perfect for football, cricket, and other sports activities.",
                'location': "Mumbai Central, Mumbai",
                'latitude': 18.9692,
                'longitude': 72.8193,
                'amenities': [
                    "Floodlights",
                    "Changing Rooms",
                    "Parking",
                    "Refreshments",
                    "First Aid",
                    "Equipment Rental"
                ],
                'rules': """1. Proper sports shoes mandatory
2. No food on the turf
3. Arrive 15 minutes before booking
4. Maintain cleanliness
5. Follow safety guidelines""",
                'opening_time': time(6, 0),
                'closing_time': time(23, 0),
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created new facility: {facility.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing facility: {facility.name}'))

        # Add sample images
        image_urls = [
            'https://images.unsplash.com/photo-1459865264687-595d652de67e',  # Soccer field at night
            'https://images.unsplash.com/photo-1565992441121-4367c2967103',  # Indoor soccer arena
            'https://images.unsplash.com/photo-1575361204480-aadea25e6e68',  # Outdoor turf field
            'https://images.unsplash.com/photo-1547347298-4074fc3086f0',  # Sports stadium
            'https://images.unsplash.com/photo-1590556409324-aa1d726e5c3c'   # Soccer field with lights
        ]

        # Delete existing images
        facility.images.all().delete()

        for i, url in enumerate(image_urls):
            try:
                response = requests.get(f'{url}?w=1200&q=80')
                if response.status_code == 200:
                    file_name = f'facility_{facility.id}_image_{i+1}.jpg'
                    facility_image = FacilityImage(
                        facility=facility,
                        is_primary=(i == 0),
                        order=i
                    )
                    facility_image.image.save(file_name, ContentFile(response.content), save=True)
                    self.stdout.write(self.style.SUCCESS(f'Added image {i+1}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error adding image {i+1}: {str(e)}'))

        # Create sport types if they don't exist
        sports_data = [
            ("Football", 1000),
            ("Cricket", 1200),
            ("Basketball", 800),
        ]

        for sport_name, price in sports_data:
            try:
                sport_type = SportType.objects.get(name=sport_name)
            except SportType.DoesNotExist:
                sport_type = SportType.objects.create(name=sport_name)
            FacilitySport.objects.get_or_create(
                facility=facility,
                sport=sport_type,
                defaults={'price_per_slot': price, 'is_available': True}
            )

        # Create time slots if they don't exist
        if not TimeSlot.objects.exists():
            slots_data = [
                ('06:00-08:00', '6 AM - 8 AM', time(6, 0), time(8, 0)),
                ('08:00-10:00', '8 AM - 10 AM', time(8, 0), time(10, 0)),
                ('10:00-12:00', '10 AM - 12 PM', time(10, 0), time(12, 0)),
                ('14:00-16:00', '2 PM - 4 PM', time(14, 0), time(16, 0)),
                ('16:00-18:00', '4 PM - 6 PM', time(16, 0), time(18, 0)),
                ('18:00-20:00', '6 PM - 8 PM', time(18, 0), time(20, 0)),
                ('20:00-22:00', '8 PM - 10 PM', time(20, 0), time(22, 0)),
            ]

            for slot_time, display, start, end in slots_data:
                TimeSlot.objects.get_or_create(
                    slot_time=slot_time,
                    defaults={
                        'start_time': start,
                        'end_time': end
                    }
                )

        # Create sample offer
        today = timezone.now().date()
        Offer.objects.get_or_create(
            facility=facility,
            title="Early Bird Special",
            defaults={
                'description': "20% off on morning slots (6 AM - 10 AM)",
                'discount_percentage': 20,
                'start_date': today,
                'end_date': today + timedelta(days=30),
                'is_active': True
            }
        )

        self.stdout.write(self.style.SUCCESS('Sample facility setup completed successfully'))