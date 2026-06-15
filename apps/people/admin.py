from django.contrib import admin

from .models import Teacher, TeacherAvailability, TeacherQualification


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "code", "email", "status", "weekly_load")
    list_filter = ("status",)
    search_fields = ("name", "code", "email", "phone_number", "notes")


@admin.register(TeacherQualification)
class TeacherQualificationAdmin(admin.ModelAdmin):
    list_display = ("teacher", "tenant", "subject", "teaching_level", "series", "unit", "status")
    list_filter = ("status",)
    search_fields = (
        "teacher__name",
        "subject__name",
        "teaching_level__name",
        "series__name",
        "unit__name",
    )


@admin.register(TeacherAvailability)
class TeacherAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("teacher", "tenant", "weekday", "start_time", "end_time", "is_available")
    list_filter = ("weekday", "is_available")
    search_fields = ("teacher__name", "reason")
