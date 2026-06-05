from django.db import models
from django.utils.translation import gettext_lazy as _
from django_tenants.models import DomainMixin, TenantMixin


class Tenant(TenantMixin):
    """
    Represents a school or school group (tenant).

    Each tenant gets its own PostgreSQL schema.
    Data isolation is guaranteed at the schema level.
    """

    name = models.CharField(
        _("nome"),
        max_length=200,
        help_text=_("Nome da escola ou rede."),
    )
    paid_until = models.DateField(_("pago ate"), null=True, blank=True)
    on_trial = models.BooleanField(_("em periodo de teste"), default=True)
    created_on = models.DateField(_("criado em"), auto_now_add=True)

    auto_create_schema = True

    class Meta:
        verbose_name = _("tenant")
        verbose_name_plural = _("tenants")

    def __str__(self):
        return self.name


class Domain(DomainMixin):
    """
    Domain associated with a tenant.

    Resolves the tenant from the request host.
    """

    class Meta:
        verbose_name = _("dominio")
        verbose_name_plural = _("dominios")

    def __str__(self):
        return self.domain
