from django import forms

from apps.schools.models import SchoolYear


class SchoolYearForm(forms.ModelForm):
    class Meta:
        model = SchoolYear
        fields = ["name", "year", "start_date", "end_date", "status", "is_active"]