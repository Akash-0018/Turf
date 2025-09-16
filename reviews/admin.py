from django.contrib import admin
from .models import Review, Reply

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_email', 'facility', 'rating', 'short_review', 'created_at', 'is_approved', 'is_featured')
    list_filter = ('is_approved', 'is_featured', 'rating', 'facility', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'facility__name', 'review_text')
    list_editable = ('is_approved', 'is_featured')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_reviews', 'unapprove_reviews', 'feature_reviews', 'unfeature_reviews']
    ordering = ('-created_at',)

    def short_review(self, obj):
        return obj.review_text[:100] + '...' if len(obj.review_text) > 100 else obj.review_text
    short_review.short_description = 'Review'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} reviews have been approved.')
    approve_reviews.short_description = "Approve selected reviews"
    
    def unapprove_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} reviews have been unapproved.')
    unapprove_reviews.short_description = "Unapprove selected reviews"
    
    def feature_reviews(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} reviews have been featured.')
    feature_reviews.short_description = "Feature selected reviews"
    
    def unfeature_reviews(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} reviews have been unfeatured.')
    unfeature_reviews.short_description = "Unfeature selected reviews"

@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ('user', 'review', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'reply_text')
    actions = ['approve_replies', 'unapprove_replies']
    
    def approve_replies(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} replies have been approved.')
    approve_replies.short_description = "Approve selected replies"
    
    def unapprove_replies(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} replies have been unapproved.')
    unapprove_replies.short_description = "Unapprove selected replies"