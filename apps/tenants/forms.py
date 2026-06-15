from django import forms


class BaseModelForm(forms.ModelForm):
    """Base form que aceita ``request`` via ``get_form_kwargs()``.

    O ``TenantMixin`` (views) passa ``request=self.request`` no kwargs.
    Forms que precisam acessar o request (p.ex. para filtrar querysets por
    tenant) devem herdar deste form em vez de ``forms.ModelForm`` diretamente.
    """

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)