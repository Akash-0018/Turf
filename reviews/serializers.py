from rest_framework import serializers
from .models import Review, Reply

class ReplySerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Reply
        fields = ['id', 'user', 'user_name', 'reply_text', 'created_at', 'is_approved']
        read_only_fields = ['user', 'is_approved']
        
    def get_user_name(self, obj):
        return obj.user.get_full_name()

class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    replies = ReplySerializer(many=True, read_only=True)
    facility_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'user_name', 'facility', 'facility_name', 'booking',
                 'rating', 'review_text', 'created_at', 'replies', 'is_approved']
        read_only_fields = ['user', 'is_approved']
        
    def get_user_name(self, obj):
        return obj.user.get_full_name()
        
    def get_facility_name(self, obj):
        return obj.facility.name