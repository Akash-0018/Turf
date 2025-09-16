from rest_framework import serializers
from .models import Facility, FacilitySport, SportType

class SportTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SportType
        fields = '__all__'

class FacilitySportSerializer(serializers.ModelSerializer):
    sport = SportTypeSerializer(read_only=True)
    
    class Meta:
        model = FacilitySport
        fields = ['id', 'facility', 'sport', 'price_per_slot', 'is_available']

class FacilitySerializer(serializers.ModelSerializer):
    sports = FacilitySportSerializer(many=True, read_only=True)
    
    class Meta:
        model = Facility
        fields = ['id', 'name', 'description', 'location', 'latitude', 'longitude', 
                'created_at', 'updated_at', 'sports', 'images']