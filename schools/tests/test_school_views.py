"""Testes das views de schools."""

import pytest
from django_base_kit.models import User

from schools.models import School


@pytest.mark.django_db
def test_detail_view_requires_login(client):
    user = User.objects.create_user(username="u1", email="u1@test.com", password="p")
    school = School.objects.create(owner=user, name="Escola A")
    response = client.get(f"/schools/{school.pk}/")
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.django_db
def test_detail_view_filters_by_owner(client):
    user_a = User.objects.create_user(username="u2", email="u2@test.com", password="p")
    user_b = User.objects.create_user(username="u3", email="u3@test.com", password="p")
    school_a = School.objects.create(owner=user_a, name="Escola A")

    client.force_login(user_b)
    response = client.get(f"/schools/{school_a.pk}/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_update_view_filters_by_owner(client):
    user_a = User.objects.create_user(username="u4", email="u4@test.com", password="p")
    user_b = User.objects.create_user(username="u5", email="u5@test.com", password="p")
    school_a = School.objects.create(owner=user_a, name="Escola A")

    client.force_login(user_b)
    response = client.get(f"/schools/{school_a.pk}/edit/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_redirect_view_redirects_to_school_detail(client):
    user = User.objects.create_user(username="u6", email="u6@test.com", password="p")
    School.objects.create(owner=user, name="Escola R")

    client.force_login(user)
    response = client.get("/")
    assert response.status_code == 302
    assert "/schools/" in response.url


@pytest.mark.django_db
def test_redirect_view_renders_no_school_template(client):
    user = User.objects.create_user(username="u7", email="u7@test.com", password="p")

    client.force_login(user)
    response = client.get("/")
    assert response.status_code == 200
    assert "escola ainda não foi cadastrada" in response.content.decode().lower()
