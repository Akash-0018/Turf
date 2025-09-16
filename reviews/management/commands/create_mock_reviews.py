from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from facilities.models import Facility
from reviews.models import Review
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Creates mock reviews for testing purposes'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=20, help='Number of reviews to create')

    def handle(self, *args, **kwargs):
        User = get_user_model()
        count = kwargs['count']
        
        # Get all facilities and users
        facilities = list(Facility.objects.all())
        users = list(User.objects.filter(is_superuser=False))
        
        if not facilities or not users:
            self.stdout.write(self.style.ERROR('No facilities or users found. Please create some first.'))
            return

        # Sample review texts
        positive_reviews = [
            "Excellent facilities and great staff! Will definitely be coming back.",
            "One of the best turfs I've played on. The pitch quality is outstanding.",
            "Perfect location and very well maintained. Highly recommended!",
            "Great experience overall. The booking process was smooth and the facility is top-notch.",
            "Amazing place for a game with friends. The artificial turf is in perfect condition.",
            "Superb lighting for evening games. Really enjoyed playing here.",
            "Very professional management and clean facilities. Worth every penny.",
            "Best turf in the area! The amenities are excellent and staff is very helpful.",
            "Really impressed with the quality of the facilities. Will be a regular here.",
            "Modern facilities with great maintenance. Perfect for our weekly games.",
        ]
        
        neutral_reviews = [
            "Decent facilities but could use better maintenance.",
            "Good location but parking can be a bit difficult.",
            "Average experience. Nothing exceptional but gets the job done.",
            "Fair pricing but limited amenities.",
            "Okay for casual games but might need improvements for serious players.",
        ]
        
        negative_reviews = [
            "Could use better maintenance of the turf.",
            "Parking facilities need improvement.",
            "The lighting could be better for evening games.",
            "Basic facilities but a bit overpriced.",
            "Average experience, expected better for the price.",
        ]

        # Create reviews
        reviews_created = 0
        current_time = timezone.now()
        
        for i in range(count):
            rating = random.choices([5,4,3,2,1], weights=[40,30,15,10,5])[0]
            
            # Select review text based on rating
            if rating >= 4:
                review_text = random.choice(positive_reviews)
            elif rating == 3:
                review_text = random.choice(neutral_reviews)
            else:
                review_text = random.choice(negative_reviews)
            
            # Create the review
            review = Review.objects.create(
                user=random.choice(users),
                facility=random.choice(facilities),
                rating=rating,
                review_text=review_text,
                created_at=current_time - timedelta(days=random.randint(0, 60)),
                is_approved=True,
                is_featured=rating >= 4 and random.random() < 0.3  # 30% chance for 4-5 star reviews to be featured
            )
            reviews_created += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {reviews_created} mock reviews')
        )