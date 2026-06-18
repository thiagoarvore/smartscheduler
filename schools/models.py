from django.conf import settings
from django.db import models
from django.urls import reverse
from django_base_kit.models import BaseModel


class School(BaseModel):
    """
    A escola de um único user.
    Relação 1:1 — cada user é dono de no máximo 1 escola.
    """

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="school",
    )
    name = models.CharField("Nome", max_length=200)
    cnpj = models.CharField("CNPJ", max_length=18, blank=True)
    phone = models.CharField("Telefone", max_length=20, blank=True)
    email = models.EmailField("E-mail de contato", blank=True)
    address = models.CharField("Endereço", max_length=255, blank=True)

    class Meta:
        verbose_name = "Escola"
        verbose_name_plural = "Escolas"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("schools:detail", kwargs={"pk": self.pk})
