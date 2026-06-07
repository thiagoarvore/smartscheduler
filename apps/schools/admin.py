from django.contrib import admin

from .models import ClassGroup, Period, Series, TeachingLevel, Unit


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "status", "code")
    list_filter = ("status",)
    search_fields = ("name", "code")


@admin.register(TeachingLevel)
class TeachingLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "order", "status", "code")
    list_filter = ("status",)
    search_fields = ("name", "code")


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "tenant", "type", "order", "status")
    list_filter = ("status", "type")
    search_fields = ("name",)


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ("name", "teaching_level", "tenant", "order", "status", "code")
    list_filter = ("status",)
    search_fields = ("name", "code")


@admin.register(ClassGroup)
class ClassGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "period", "series", "tenant", "status", "code")
    list_filter = ("status",)
    search_fields = ("name", "code")
