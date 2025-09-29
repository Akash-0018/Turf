from django.contrib.auth.models import AbstractUser
from django.db import models

class PlayerProfile(models.Model):
    SPORT_CHOICES = [
        ('cricket', 'Cricket'),
        ('football', 'Football')
    ]
    
    PLAYING_SIDE = [
        ('right', 'Right Handed'),
        ('left', 'Left Handed')
    ]
    
    # Cricket Specific
    BATTING_STYLE = [
        ('opening', 'Opening Batsman'),
        ('top_order', 'Top Order Batsman'),
        ('middle_order', 'Middle Order Batsman'),
        ('finisher', 'Finisher'),
        ('all_rounder', 'All-Rounder')
    ]
    
    BOWLING_STYLE = [
        ('fast', 'Fast Bowler'),
        ('medium_fast', 'Medium Fast'),
        ('off_break', 'Off Break'),
        ('leg_break', 'Leg Break')
    ]
    
    # Football Specific
    FOOTBALL_POSITION = [
        ('goalkeeper', 'Goalkeeper'),
        ('defender', 'Defender'),
        ('midfielder', 'Midfielder'),
        ('forward', 'Forward')
    ]
    
    FOOTBALL_STYLE = [
        ('striker', 'Striker'),
        ('winger', 'Winger'),
        ('attacking_mid', 'Attacking Midfielder'),
        ('defensive_mid', 'Defensive Midfielder'),
        ('center_back', 'Center Back'),
        ('full_back', 'Full Back'),
        ('sweeper', 'Sweeper')
    ]

    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='player_profile')
    preferred_sport = models.CharField(max_length=20, choices=SPORT_CHOICES)
    playing_side = models.CharField(max_length=10, choices=PLAYING_SIDE)
    
    # Cricket fields
    is_wicketkeeper = models.BooleanField(default=False)
    batting_style = models.CharField(max_length=20, choices=BATTING_STYLE, null=True, blank=True)
    bowling_style = models.CharField(max_length=20, choices=BOWLING_STYLE, null=True, blank=True)
    
    # Football fields
    football_position = models.CharField(max_length=20, choices=FOOTBALL_POSITION, null=True, blank=True)
    football_style = models.CharField(max_length=20, choices=FOOTBALL_STYLE, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Player Profile"

    def get_sport_details(self):
        if self.preferred_sport == 'cricket':
            details = []
            side = 'Left Handed' if self.playing_side == 'left' else 'Right Handed'
            
            if self.batting_style:
                details.append(f"{side} {dict(self.BATTING_STYLE)[self.batting_style]}")
            if self.bowling_style:
                details.append(f"{side} {dict(self.BOWLING_STYLE)[self.bowling_style]}")
            if self.is_wicketkeeper:
                details.append("Wicketkeeper")
            
            return " | ".join(details)
        else:  # Football
            details = []
            if self.football_position:
                details.append(dict(self.FOOTBALL_POSITION)[self.football_position])
            if self.football_style:
                details.append(dict(self.FOOTBALL_STYLE)[self.football_style])
            return " | ".join(details)

class User(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'auth_user'
        
    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        # If the user is a superuser, automatically make them an admin
        if self.is_superuser:
            self.is_admin = True
        super().save(*args, **kwargs)
