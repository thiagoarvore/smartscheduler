from django import forms

from .models import CurriculumMatrix, Subject


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["code", "name", "slug", "status"]


class CurriculumMatrixForm(forms.ModelForm):
    class Meta:
        model = CurriculumMatrix
        fields = ["name", "teaching_level", "series", "version", "status", "effective_from", "effective_to"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, "request") and self.request:
            from apps.schools.models import Series, TeachingLevel

            tenant = self.request.tenant
            self.fields["teaching_level"].queryset = TeachingLevel.objects.filter(tenant=tenant)
            self.fields["series"].queryset = Series.objects.filter(tenant=tenant)