from django import forms

from apps.schools.models import SchoolYear
from apps.tenants.forms import BaseModelForm


class SchoolYearForm(BaseModelForm):
    class Meta:
        model = SchoolYear
        fields = ["name", "year", "start_date", "end_date", "status", "is_active"]