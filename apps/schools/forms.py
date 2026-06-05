from django import forms

from .models import ClassGroup, Period, Series, TeachingLevel, Unit


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ["tenant", "code", "name", "status", "timezone", "default_settings"]


class TeachingLevelForm(forms.ModelForm):
    class Meta:
        model = TeachingLevel
        fields = ["tenant", "code", "name", "order", "status"]


class PeriodForm(forms.ModelForm):
    class Meta:
        model = Period
        fields = ["tenant", "unit", "name", "type", "order", "status", "start_time", "end_time"]


class SeriesForm(forms.ModelForm):
    class Meta:
        model = Series
        fields = ["tenant", "teaching_level", "code", "name", "order", "status"]


class ClassGroupForm(forms.ModelForm):
    class Meta:
        model = ClassGroup
        fields = ["tenant", "unit", "period", "series", "code", "name", "status"]
