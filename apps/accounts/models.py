import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom user model for Grade Certa.

    Uses email as the primary authentication identifier.
    UUID primary key, audit-friendly fields.
    """

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    email = models.EmailField(
        _("e-mail"),
        unique=True,
        error_messages={
            "unique": _("Ja existe um usuario com este e-mail."),
        },
    )
    active = models.BooleanField(
        _("ativo"),
        default=True,
        help_text=_("Indica se o usuario deve ser tratado como ativo."),
    )

    # Override reverse accessors to avoid clash with django-base-kit's User
    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name=_("grupos"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="accounts_user_set",
        related_query_name="accounts_user",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name=_("permissoes"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="accounts_user_set",
        related_query_name="accounts_user",
    )

    # Make email the USERNAME_FIELD for authentication
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("usuario")
        verbose_name_plural = _("usuarios")
        ordering = ["first_name", "email"]

    def __str__(self):
        return self.email
