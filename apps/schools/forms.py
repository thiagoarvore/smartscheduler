from django import forms

from .models import ClassGroup, Period, Series, TeachingLevel, Unit

BRAZIL_TIMEZONES = [
    ("America/Sao_Paulo", "Brasília (São Paulo)"),
    ("America/Rio_Branco", "Acre (Rio Branco)"),
    ("America/Manaus", "Amazonas (Manaus)"),
    ("America/Porto_Velho", "Rondônia (Porto Velho)"),
    ("America/Boa_Vista", "Roraima (Boa Vista)"),
    ("America/Cuiaba", "Mato Grosso (Cuiabá)"),
    ("America/Campo_Grande", "Mato Grosso do Sul (Campo Grande)"),
    ("America/Belem", "Pará (Belém)"),
    ("America/Fortaleza", "Nordeste (Fortaleza)"),
    ("America/Recife", "Nordeste (Recife)"),
    ("America/Bahia", "Bahia (Salvador)"),
    ("America/Noronha", "Fernando de Noronha"),
]


class UnitForm(forms.ModelForm):
    timezone = forms.ChoiceField(
        label="Fuso horário",
        choices=BRAZIL_TIMEZONES,
        initial="America/Sao_Paulo",
        required=False,
    )

    class Meta:
        model = Unit
        fields = ["code", "name", "address", "status", "timezone"]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 2}),
        }


class TeachingLevelForm(forms.ModelForm):
    class Meta:
        model = TeachingLevel
        fields = ["code", "name", "order", "status"]


class PeriodForm(forms.ModelForm):
    class Meta:
        model = Period
        fields = ["name", "type", "order", "status", "start_time", "end_time", "is_tenant_default", "units"]
        widgets = {
            "units": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        if self.request:
            self.fields["units"].queryset = Unit.objects.filter(tenant=self.request.tenant)
        # For tenant-default periods, units is optional
        self.fields["units"].required = False


class SeriesForm(forms.ModelForm):
    class Meta:
        model = Series
        fields = ["teaching_level", "code", "name", "order", "status", "is_tenant_default", "units"]
        widgets = {
            "units": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        if self.request:
            tenant = self.request.tenant
            self.fields["teaching_level"].queryset = TeachingLevel.objects.filter(tenant=tenant)
            self.fields["units"].queryset = Unit.objects.filter(tenant=tenant)
        self.fields["units"].required = False


class ClassGroupForm(forms.ModelForm):
    class Meta:
        model = ClassGroup
        fields = ["unit", "period", "series", "code", "name", "status"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        if self.request:
            tenant = self.request.tenant
            self.fields["unit"].queryset = Unit.objects.filter(tenant=tenant)
            self.fields["period"].queryset = Period.objects.filter(tenant=tenant)
            self.fields["series"].queryset = Series.objects.filter(tenant=tenant)