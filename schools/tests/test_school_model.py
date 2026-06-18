"""Testes do modelo School."""

import pytest
from django_base_kit.models import User

from schools.models import School


@pytest.mark.django_db
def test_school_str_returns_name():
    user = User.objects.create_user(username="owner1", email="owner1@test.com", password="p")
    school = School.objects.create(owner=user, name="Escola Teste")
    assert str(school) == "Escola Teste"


@pytest.mark.django_db
def test_school_has_one_to_one_owner():
    user = User.objects.create_user(username="owner2", email="owner2@test.com", password="p")
    school = School.objects.create(owner=user, name="Escola Dois")
    assert user.school == school
