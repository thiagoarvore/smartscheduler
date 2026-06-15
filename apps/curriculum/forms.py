from django import forms

from apps.schools.models import Series, TeachingLevel
from apps.tenants.forms import BaseModelForm
from .models import CurriculumMatrix, Subject


class SubjectForm(BaseModelForm):
    class Meta:
        model = Subject
        fields = ["code", "name", "slug", "status"]


class CurriculumMatrixForm(BaseModelForm):
    class Meta:
        model = CurriculumMatrix
        fields = ["name", "teaching_level", "series", "version", "status", "effective_from", "effective_to"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.request:
            tenant = self.request.tenant
            self.fields["teaching_level"].queryset = TeachingLevel.objects.filter(tenant=tenant)
            self.fields["series"].queryset = Series.objects.filter(tenant=tenant)