import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
class TestLoginView:
    """Tests for the login view."""

    def test_login_page_renders(self):
        client = Client()
        response = client.get(reverse("login"))
        assert response.status_code == 200
        assert "Grade Certa" in response.content.decode()

    def test_login_with_valid_credentials(self):
        User.objects.create_user(
            username="testuser",
            email="login@gradecerta.com",
            password="testpass12345",
        )
        client = Client()
        response = client.post(
            reverse("login"),
            {"username": "login@gradecerta.com", "password": "testpass12345"},
        )
        assert response.status_code == 302
        assert response.url == "/"

    def test_login_with_invalid_credentials(self):
        client = Client()
        response = client.post(
            reverse("login"),
            {"username": "nobody@gradecerta.com", "password": "wrongpass"},
        )
        assert response.status_code == 200  # Re-renders form


@pytest.mark.django_db
class TestHomeView:
    """Tests for the home view."""

    def test_home_requires_login(self):
        client = Client()
        response = client.get(reverse("home"))
        assert response.status_code == 302  # Redirects to login

    def test_home_accessible_after_login(self):
        user = User.objects.create_user(
            username="testuser",
            email="home@gradecerta.com",
            password="testpass12345",
        )
        client = Client()
        client.force_login(user)
        response = client.get(reverse("home"))
        assert response.status_code == 200
