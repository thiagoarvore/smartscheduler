"""Testes do SchoolMiddleware."""

import pytest
from django.test import RequestFactory
from django_base_kit.models import User

from schools.middleware import SchoolMiddleware
from schools.models import School


@pytest.fixture
def middleware():
    return SchoolMiddleware(lambda req: None)


@pytest.fixture
def factory():
    return RequestFactory()


@pytest.mark.django_db
def test_middleware_sets_school_for_authenticated_user_with_school(middleware, factory):
    user = User.objects.create_user(username="mw1", email="mw1@test.com", password="p")
    school = School.objects.create(owner=user, name="Escola MW1")

    request = factory.get("/some/path/")
    request.user = user
    middleware.process_request(request)

    assert request.school == school


@pytest.mark.django_db
def test_middleware_sets_school_none_for_user_without_school(middleware, factory):
    user = User.objects.create_user(username="mw2", email="mw2@test.com", password="p")

    request = factory.get("/some/path/")
    request.user = user
    middleware.process_request(request)

    assert request.school is None


@pytest.mark.django_db
def test_middleware_skips_anon_user(middleware, factory):
    from django.contrib.auth.models import AnonymousUser

    request = factory.get("/some/path/")
    request.user = AnonymousUser()
    middleware.process_request(request)

    assert request.school is None


@pytest.mark.django_db
def test_middleware_skips_public_paths(middleware, factory):
    user = User.objects.create_user(username="mw3", email="mw3@test.com", password="p")
    School.objects.create(owner=user, name="Escola MW3")

    for public_path in ["/health/", "/admin/", "/accounts/login/"]:
        request = factory.get(public_path)
        request.user = user
        middleware.process_request(request)
        assert request.school is None, f"Path {public_path} should be public"
