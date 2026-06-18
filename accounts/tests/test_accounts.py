"""Testes do app accounts — User do base_kit + signup removido."""

import pytest
from django.db import IntegrityError
from django_base_kit.models import User


@pytest.mark.django_db
def test_user_email_is_unique():
    """User criado (via admin) tem email único — validação do base_kit."""
    User.objects.create_user(username="alice", email="alice@example.com", password="test123")
    with pytest.raises(IntegrityError):
        User.objects.create_user(username="bob", email="alice@example.com", password="test456")


@pytest.mark.django_db
def test_signup_url_does_not_exist(client):
    """/accounts/signup/ retorna 404 — rota foi removida."""
    response = client.get("/accounts/signup/")
    assert response.status_code == 404
