from django.core.management.base import BaseCommand
import qrcode
from pathlib import Path
from django.conf import settings

class Command(BaseCommand):
    help = 'Generate sample payment QR code'

    def handle(self, *args, **kwargs):
        # Sample UPI ID
        upi_data = "upi://pay?pa=turfzone@upi&pn=TurfZone%20Sports&cu=INR"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(upi_data)
        qr.make(fit=True)

        # Create QR image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        samples_dir = Path(settings.BASE_DIR) / 'static' / 'images' / 'samples'
        samples_dir.mkdir(parents=True, exist_ok=True)
        qr_path = samples_dir / 'qr_code.png'
        qr_image.save(qr_path)

        self.stdout.write(self.style.SUCCESS('Successfully generated sample QR code'))