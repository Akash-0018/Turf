from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from facilities.models import Facility, FacilityImage
import os
from pathlib import Path

class Command(BaseCommand):
    help = 'Add sample facility images'

    def handle(self, *args, **kwargs):
        # Sample images in static/images/samples
        sample_images = ['turf1.jpg', 'turf2.jpg', 'turf3.jpg']
        
        # Get all facilities
        facilities = Facility.objects.all()
        
        for facility in facilities:
            for i, img_name in enumerate(sample_images):
                # Source image path
                src_path = Path(settings.BASE_DIR) / 'static' / 'images' / 'samples' / img_name
                
                if src_path.exists():
                    # Create facility image
                    img = FacilityImage.objects.create(
                        facility=facility,
                        is_primary=(i == 0),  # First image is primary
                        order=i
                    )
                    
                    # Copy image to media directory
                    dst_path = Path(settings.MEDIA_ROOT) / 'facilities' / img_name
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(src_path, 'rb') as src_file:
                        img.image.save(img_name, File(src_file), save=True)
                        
        self.stdout.write(self.style.SUCCESS('Successfully added sample facility images'))