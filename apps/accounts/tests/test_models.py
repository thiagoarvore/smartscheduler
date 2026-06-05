import uuid

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Tests for the custom User model."""

    def test_create_user_with_email(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@gradecerta.com",
            password="testpass12345",
        )
        assert user.pk is not None
        assert isinstance(user.pk, uuid.UUID)
        assert user.email == "test@gradecerta.com"
        assert user.active is True
        assert user.check_password("testpass12345")

    def test_email_is_unique(self):
        User.objects.create_user(
            username="user1",
            email="unique@gradecerta.com",
            password="testpass12345",
        )
        with pytest.raises(Exception):  # noqa: B017
            User.objects.create_user(
                username="user2",
                email="unique@gradecerta.com",
                password="testpass12345",
            )

    def test_email_is_username_field(self):
        assert User.USERNAME_FIELD == "email"

    def test_str_returns_email(self):
        user = User.objects.create_user(
            username="testuser",
            email="strtest@gradecerta.com",
            password="testpass12345",
        )
        assert str(user) == "strtest@gradecerta.com"

    def test_user_defaults_to_active(self):
        user = User.objects.create_user(
            username="testuser",
            email="active@gradecerta.com",
            password="testpass12345",
        )
        assert user.active is True

    def test_user_uuid_primary_key(self):
        user = User.objects.create_user(
            username="testuser",
            email="uuid@gradecerta.com",
            password="testpass12345",
        )
        assert isinstance(user.pk, uuid.UUID)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@gradecerta.com",
            password="adminpass12345",
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True
