from django import forms
from django.contrib.auth import get_user_model
from .models import Team, TeamMember

User = get_user_model()

class AddPlayerForm(forms.Form):
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number',
            'type': 'tel',
            'pattern': '[0-9]{10}',
            'title': 'Enter a valid 10-digit phone number',
            'autocomplete': 'off'  # Prevent browser autocomplete from interfering
        })
    )

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        # Remove any spaces or special characters
        phone_number = ''.join(filter(str.isdigit, phone_number))
        
        try:
            users = User.objects.filter(phone_number=phone_number)
            if not users.exists():
                raise forms.ValidationError('No user found with this phone number. Please check and try again.')
            if users.count() > 1:
                raise forms.ValidationError('Multiple users found with this phone number. Please contact support.')
            return phone_number
        except User.DoesNotExist:
            raise forms.ValidationError('No user found with this phone number. Please check and try again.')

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'logo']
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        team = super().save(commit=False)
        if not team.captain and self.user:
            team.captain = self.user
        if commit:
            team.save()
            # Create captain membership
            TeamMember.objects.create(
                team=team,
                user=team.captain,
                role='captain'
            )
        return team

class TeamManagementForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'logo', 'vice_captain']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'vice_captain': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select Vice Captain'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            # Get eligible team members for vice captain (excluding captain)
            team_members = TeamMember.objects.filter(
                team=self.instance,
                is_active=True
            ).exclude(user=self.instance.captain).select_related('user')
            
            # Create choices with user information
            choices = [(None, '-- Select Vice Captain --')]
            choices.extend([
                (member.user.id, f"{member.user.get_full_name() or member.user.username}")
                for member in team_members
            ])
            
            self.fields['vice_captain'].choices = choices
            self.fields['vice_captain'].required = False
            
            # Add help text
            self.fields['vice_captain'].help_text = 'Select a team member to be vice captain'