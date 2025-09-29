from django import forms
from .models import Facility, SportType, FacilitySport

class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = [
            'name', 'description', 'location', 'google_maps_link',
            'amenities', 'rules', 'opening_time', 'closing_time'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'google_maps_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.google.com/maps?q=...'
            }),
            'rules': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'opening_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'closing_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
        }

    def clean_google_maps_link(self):
        link = self.cleaned_data.get('google_maps_link')
        if link and not ('google.com/maps' in link or 'goo.gl/maps' in link):
            raise forms.ValidationError('Please enter a valid Google Maps link')
        return link

class SportTypeForm(forms.ModelForm):
    class Meta:
        model = SportType
        fields = ['name', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'icon': forms.FileInput(attrs={'class': 'form-control'})
        }

class FacilitySportForm(forms.ModelForm):
    class Meta:
        model = FacilitySport
        fields = ['sport', 'price_per_slot', 'is_available']
        widgets = {
            'sport': forms.Select(attrs={'class': 'form-select'}),
            'price_per_slot': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            }),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class SportManagementForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        
        # Add form fields for new sport
        self.fields['sport'] = forms.ModelChoiceField(
            queryset=SportType.objects.exclude(
                id__in=FacilitySport.objects.filter(
                    facility=self.instance
                ).values_list('sport_id', flat=True)
            ) if self.instance else SportType.objects.none(),
            required=False,
            widget=forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select a sport'
            })
        )
        self.fields['price_per_slot'] = forms.DecimalField(
            required=False,
            widget=forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            })
        )
        self.fields['max_players'] = forms.IntegerField(
            min_value=1,
            required=False,
            widget=forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            })
        )
        self.fields['is_available'] = forms.BooleanField(
            required=False,
            initial=True,
            widget=forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        )
    
    def clean(self):
        cleaned_data = super().clean()
        sport = cleaned_data.get('sport')
        price = cleaned_data.get('price_per_slot')
        max_players = cleaned_data.get('max_players')
        
        if sport:
            if not price:
                self.add_error('price_per_slot', "Price per slot is required when adding a sport")
            if not max_players:
                self.add_error('max_players', "Maximum number of players is required when adding a sport")
        elif any([price, max_players]):
            raise forms.ValidationError("Cannot set price or max players without selecting a sport")
        
        return cleaned_data
    
    def save(self):
        if not self.instance:
            raise ValueError("Form instance is required to save")
        
        if self.cleaned_data.get('sport'):
            # Create new facility sport
            FacilitySport.objects.create(
                facility=self.instance,
                sport=self.cleaned_data['sport'],
                price_per_slot=self.cleaned_data['price_per_slot'],
                max_players=self.cleaned_data['max_players'],
                is_available=self.cleaned_data['is_available']
            )