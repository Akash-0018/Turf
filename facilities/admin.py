from django.contrib import admin
from django.utils.html import format_html
from .models import (
    SiteSettings,
    Facility,
    FacilityImage,
    SportType,
    FacilitySport,
    Offer,
    TimeSlot
)

class FacilityImageInline(admin.TabularInline):
    model = FacilityImage
    extra = 1
    fields = ('image', 'is_primary', 'order')
    classes = ('collapse',)

class FacilitySportInline(admin.TabularInline):
    model = FacilitySport
    extra = 1
    classes = ('collapse',)

class OfferInline(admin.TabularInline):
    model = Offer
    extra = 1
    classes = ('collapse',)

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'is_active', 'display_primary_image', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'location')
    inlines = [FacilityImageInline, FacilitySportInline, OfferInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Location', {
            'fields': ('location', 'latitude', 'longitude'),
        }),
        ('Operating Hours', {
            'fields': ('opening_time', 'closing_time'),
        }),
        ('Additional Information', {
            'fields': ('amenities', 'rules'),
            'classes': ('collapse',),
        }),
    )

    def display_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return format_html('<img src="{}" style="max-height: 50px;" />', primary_image.image.url)
        return "No image"
    display_primary_image.short_description = 'Primary Image'

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Site Identity', {
            'fields': ('site_name', 'logo', 'favicon')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone')
        }),
        ('Content', {
            'fields': ('about_us', 'terms_conditions', 'privacy_policy')
        }),
        ('Booking Settings', {
            'fields': ('booking_time_limit', 'cancellation_time_limit', 'max_advance_booking_days')
        }),
        ('System Settings', {
            'fields': ('maintenance_mode', 'social_links'),
        }),
    )

    def has_add_permission(self, request):
        # Prevent creating multiple settings instances
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deleting the settings instance
        return False

@admin.register(SportType)
class SportTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_icon')
    search_fields = ('name',)

    def display_icon(self, obj):
        if obj.icon:
            return format_html('<img src="{}" style="max-height: 30px;" />', obj.icon.url)
        return "No icon"
    display_icon.short_description = 'Icon'

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('slot_time', 'start_time', 'end_time')
    list_filter = ('start_time',)
    ordering = ('start_time',)