from django.contrib import admin

from .models import (
    CurriculumMatrix,
    InheritanceRule,
    LocalException,
    Subject,
    SubjectRule,
    WorkloadItem,
)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "code", "slug", "status")
    list_filter = ("status",)
    search_fields = ("name", "code", "slug")


@admin.register(CurriculumMatrix)
class CurriculumMatrixAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "teaching_level", "series", "version", "status")
    list_filter = ("status",)
    search_fields = ("name", "version")


@admin.register(WorkloadItem)
class WorkloadItemAdmin(admin.ModelAdmin):
    list_display = (
        "curriculum_matrix",
        "subject",
        "series",
        "class_group",
        "weekly_lessons",
        "lesson_duration_min",
        "is_double_lesson",
        "can_share",
    )
    list_filter = ("is_double_lesson", "can_share")
    search_fields = ("subject__name", "curriculum_matrix__name", "notes")


@admin.register(SubjectRule)
class SubjectRuleAdmin(admin.ModelAdmin):
    list_display = ("rule_type", "tenant", "is_active")
    list_filter = ("rule_type", "is_active")


@admin.register(InheritanceRule)
class InheritanceRuleAdmin(admin.ModelAdmin):
    list_display = ("rule_type", "tenant", "source_type", "target_type", "priority", "is_active")
    list_filter = ("rule_type", "is_active", "source_type", "target_type")


@admin.register(LocalException)
class LocalExceptionAdmin(admin.ModelAdmin):
    list_display = ("tenant", "inheritance_rule", "scope_type", "reason", "is_active")
    list_filter = ("scope_type", "is_active")
    search_fields = ("reason",)
