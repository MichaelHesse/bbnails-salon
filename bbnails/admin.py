from django.contrib import admin
from .models import GalleryImage, Service, BookingSlot, Appointment


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active')
    list_filter = ('is_active',)


@admin.register(BookingSlot)
class BookingSlotAdmin(admin.ModelAdmin):
    list_display = ('time_slot', 'is_available')
    list_filter = ('is_available',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'service', 'preferred_date', 'time_slot', 'status')
    list_filter = ('status', 'preferred_date')
    search_fields = ('full_name', 'phone_number', 'service')