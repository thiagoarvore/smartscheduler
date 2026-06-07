from django import forms

from .models import Teacher, TeacherAvailability, TeacherQualification


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ["tenant", "code", "name", "email", "phone_number", "status", "max_weekly_load", "notes"]


class TeacherQualificationForm(forms.ModelForm):
    class Meta:
        model = TeacherQualification
        fields = [
            "tenant",
            "teacher",
            "subject",
            "teaching_level",
            "series",
            "unit",
            "valid_from",
            "valid_until",
            "status",
        ]


class TeacherAvailabilityForm(forms.ModelForm):
    class Meta:
        model = TeacherAvailability
        fields = ["tenant", "teacher", "weekday", "start_time", "end_time", "is_available", "reason"]
