from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=True)
    address = forms.CharField(widget=forms.Textarea, required=True)
    profile_picture = forms.ImageField(required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'phone_number', 'address', 'profile_picture')

from sport_teams.models import Team

PREFERRED_SPORT_CHOICES = [
    ('cricket', 'Cricket'),
    ('football', 'Football')
]

PLAYING_SIDE_CHOICES = [
    ('right', 'Right'),
    ('left', 'Left')
]

BATTING_STYLE_CHOICES = [
    ('right', 'Right-handed'),
    ('left', 'Left-handed')
]

BOWLING_STYLE_CHOICES = [
    ('fast', 'Fast'),
    ('medium', 'Medium'),
    ('spin', 'Spin')
]

FOOTBALL_POSITION_CHOICES = [
    ('goalkeeper', 'Goalkeeper'),
    ('defender', 'Defender'),
    ('midfielder', 'Midfielder'),
    ('forward', 'Forward')
]

FOOTBALL_STYLE_CHOICES = [
    ('attacking', 'Attacking'),
    ('defensive', 'Defensive'),
    ('all_round', 'All-round')
]

class CustomUserChangeForm(UserChangeForm):
    # Remove the password field from the form
    password = None
    
    # Basic Information
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    username = forms.CharField(
        max_length=150, 
        required=True,
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        help_text='Enter a valid phone number'
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text='Upload a profile picture'
    )
    
    # Sport Preferences
    preferred_sport = forms.ChoiceField(
        choices=PREFERRED_SPORT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select your preferred sport'
    )
    playing_side = forms.ChoiceField(
        choices=PLAYING_SIDE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select your playing side'
    )
    
    # Cricket-specific fields
    batting_style = forms.ChoiceField(
        choices=BATTING_STYLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select your batting style'
    )
    bowling_style = forms.ChoiceField(
        choices=BOWLING_STYLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select your bowling style'
    )
    is_wicketkeeper = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Check if you are a wicketkeeper'
    )
    
    # Football-specific fields
    football_position = forms.ChoiceField(
        choices=FOOTBALL_POSITION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select your preferred position'
    )
    football_style = forms.ChoiceField(
        choices=FOOTBALL_STYLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select your playing style'
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone_number', 'profile_picture',
            'preferred_sport', 'playing_side',
            'batting_style', 'bowling_style', 'is_wicketkeeper',
            'football_position', 'football_style'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field in self.fields.values():
            if not isinstance(field.widget, forms.FileInput):
                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs.update({'class': 'form-check-input'})
                else:
                    field.widget.attrs.update({'class': 'form-control'})
                    
        # Get the current user's sport preference
        if self.instance and hasattr(self.instance, 'player_profile'):
            preferred_sport = self.instance.player_profile.preferred_sport
        else:
            preferred_sport = None
            
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email
        
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
            raise forms.ValidationError('This username is already in use.')
        return username