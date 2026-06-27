from django.contrib import admin

from apps.bookings.models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("user", "session", "gym", "status", "created_at")
    list_filter = ("gym", "status", "session__course")
    search_fields = ("user__username", "session__course__name")
    autocomplete_fields = ("user", "session", "gym")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
