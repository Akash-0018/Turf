from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files import File
from django.conf import settings
from facilities.models import Facility, SportType, FacilitySport, TimeSlot
from payments.models import PaymentSettings
from pathlib import Path
import shutil
import os

class Command(BaseCommand):
    help = 'Add sample data for testing'

    def handle(self, *args, **kwargs):
        # Create Sport Types
        sports = {
            'Football': 'football.jpg',
            'Cricket': 'cricket.jpg',
            'Basketball': 'basketball.jpg',
        }
        
        for sport_name, image_name in sports.items():
            sport = SportType.objects.create(name=sport_name)
            
            # Copy sample image
            src_path = Path(settings.BASE_DIR) / 'static' / 'images' / 'samples' / image_name
            if src_path.exists():
                dst_path = Path(settings.MEDIA_ROOT) / 'sports' / image_name
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(src_path, dst_path)
                sport.icon.name = f'sports/{image_name}'
                sport.save()

        # Create Time Slots
        slots = [
            ('06:00-08:00', '06:00', '08:00'),
            ('08:00-10:00', '08:00', '10:00'),
            ('10:00-12:00', '10:00', '12:00'),
            ('12:00-13:00', '12:00', '13:00'),  # Lunch break
            ('14:00-16:00', '14:00', '16:00'),
            ('16:00-18:00', '16:00', '18:00'),
            ('18:00-20:00', '18:00', '20:00'),
            ('20:00-22:00', '20:00', '22:00'),
        ]
        
        for slot_time, start, end in slots:
            TimeSlot.objects.get_or_create(
                slot_time=slot_time,
                start_time=start,
                end_time=end
            )

        # Create Facilities
        facilities = [
            {
                'name': 'TurfZone Arena 1',
                'description': 'Premium sports facility with modern amenities',
                'location': 'Mumbai Central',
                'image': 'facility1.jpg'
            },
            {
                'name': 'TurfZone Arena 2',
                'description': 'State-of-the-art sports complex',
                'location': 'Andheri West',
                'image': 'facility2.jpg'
            }
        ]
        
        for facility_data in facilities:
            facility = Facility.objects.create(
                name=facility_data['name'],
                description=facility_data['description'],
                location=facility_data['location'],
            )
            
            # Copy sample image
            src_path = Path(settings.BASE_DIR) / 'static' / 'images' / 'samples' / facility_data['image']
            if src_path.exists():
                dst_path = Path(settings.MEDIA_ROOT) / 'facilities' / facility_data['image']
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(src_path, dst_path)
                facility.image.name = f'facilities/{facility_data["image"]}'
                facility.save()

            # Create Facility Sports
            for sport in SportType.objects.all():
                FacilitySport.objects.create(
                    facility=facility,
                    sport=sport,
                    price_per_slot=1000 if sport.name == 'Football' else 800,
                    is_available=True
                )

        # Create Payment Settings
        payment_settings = PaymentSettings.objects.create(
            merchant_name='TurfZone Sports',
            upi_id='turfzone@upi',
            is_active=True
        )
        
        # Copy sample QR code
        src_path = Path(settings.BASE_DIR) / 'static' / 'images' / 'samples' / 'qr_code.png'
        if src_path.exists():
            dst_path = Path(settings.MEDIA_ROOT) / 'payment_qr' / 'qr_code.png'
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src_path, dst_path)
            payment_settings.qr_code.name = 'payment_qr/qr_code.png'
            payment_settings.save()

        self.stdout.write(self.style.SUCCESS('Successfully added sample data'))