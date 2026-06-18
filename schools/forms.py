from django import forms

from .models import School


class SchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = ["name", "cnpj", "phone", "email", "address"]
        labels = {
            "name": "Nome da escola",
            "cnpj": "CNPJ",
            "phone": "Telefone",
            "email": "E-mail de contato",
            "address": "Endereço",
        }
