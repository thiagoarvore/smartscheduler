"""Forms for managing user accounts."""

from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)
from django.utils.translation import gettext_lazy as _

from .models import User


class SignUpForm(UserCreationForm):
    """Form for registering new users."""

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = _("Nome de usuario")
        self.fields["email"].label = _("Endereco de e-mail")
        self.fields["password1"].label = _("Senha")
        self.fields["password2"].label = _("Confirmacao de senha")


class UserLoginForm(AuthenticationForm):
    """Form for user authentication via email."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = _("E-mail")
        self.fields["password"].label = _("Senha")
