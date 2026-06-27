from django.contrib import admin

from apps.courses.models import Course, CourseSession


class CourseSessionInline(admin.TabularInline):
    model = CourseSession
    extra = 0
    exclude = ("gym",)
    fields = ("starts_at", "ends_at", "capacity", "status")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "gym", "level", "default_capacity", "is_active", "created_at")
    list_filter = ("gym", "level", "is_active")
    search_fields = ("name", "instructor_name")
    autocomplete_fields = ("gym",)
    inlines = (CourseSessionInline,)
    ordering = ("gym", "name")


@admin.register(CourseSession)
class CourseSessionAdmin(admin.ModelAdmin):
    list_display = (
        "course",
        "gym",
        "starts_at",
        "ends_at",
        "status",
        "capacity",
    )
    list_filter = ("gym", "status", "course")
    search_fields = ("course__name",)
    autocomplete_fields = ("gym", "course")
    date_hierarchy = "starts_at"
    ordering = ("-starts_at",)
    readonly_fields = ("created_at", "updated_at")
