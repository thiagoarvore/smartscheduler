from django import forms

from .models import Teacher, TeacherAvailability, TeacherQualification


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ["code", "name", "email", "phone_number", "status", "weekly_load", "notes"]


class TeacherQualificationForm(forms.ModelForm):
    class Meta:
        model = TeacherQualification
        fields = [
            "teacher",
            "subject",
            "teaching_level",
            "series",
            "unit",
            "valid_from",
            "valid_until",
            "status",
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        if self.request:
            from apps.schools.models import TeachingLevel, Unit
            from apps.curriculum.models import Subject

            tenant = self.request.tenant
            self.fields["teacher"].queryset = Teacher.objects.filter(tenant=tenant)
            self.fields["subject"].queryset = Subject.objects.filter(tenant=tenant)
            self.fields["teaching_level"].queryset = TeachingLevel.objects.filter(tenant=tenant)
            self.fields["series"].queryset = TeachingLevel.objects.none()  # Filter by teaching_level change
            self.fields["unit"].queryset = Unit.objects.filter(tenant=tenant)

            # Filter series based on selected teaching_level if editing
            if self.instance and self.instance.pk and self.instance.teaching_level_id:
                from apps.schools.models import Series

                self.fields["series"].queryset = Series.objects.filter(
                    tenant=tenant, teaching_level_id=self.instance.teaching_level_id
                )


class TeacherAvailabilityForm(forms.ModelForm):
    class Meta:
        model = TeacherAvailability
        fields = ["teacher", "weekday", "start_time", "end_time", "is_available", "reason"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        if self.request:
            self.fields["teacher"].queryset = Teacher.objects.filter(tenant=self.request.tenant)