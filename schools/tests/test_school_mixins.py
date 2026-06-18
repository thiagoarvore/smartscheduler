"""Testes do SchoolScopedQuerysetMixin."""

import pytest
from django.test import RequestFactory
from django.views.generic import ListView
from django_base_kit.models import User

from schools.mixins import SchoolScopedQuerysetMixin
from schools.models import School


class DummyListView(SchoolScopedQuerysetMixin, ListView):
    """ListView fake que herda o mixin para testar o filtro."""

    model = School


@pytest.fixture
def factory():
    return RequestFactory()


@pytest.mark.django_db
def test_mixin_filters_queryset_by_owner(factory):
    user_a = User.objects.create_user(username="mx1", email="mx1@test.com", password="p")
    user_b = User.objects.create_user(username="mx2", email="mx2@test.com", password="p")
    School.objects.create(owner=user_a, name="Escola A")
    School.objects.create(owner=user_b, name="Escola B")

    view = DummyListView()
    view.request = factory.get("/")
    view.request.user = user_a

    qs = view.get_queryset()
    assert qs.count() == 1
    assert qs.first().owner == user_a


@pytest.mark.django_db
def test_mixin_returns_empty_for_anon_user(factory):
    from django.contrib.auth.models import AnonymousUser

    user = User.objects.create_user(username="mx3", email="mx3@test.com", password="p")
    School.objects.create(owner=user, name="Escola C")

    view = DummyListView()
    view.request = factory.get("/")
    view.request.user = AnonymousUser()

    qs = view.get_queryset()
    assert qs.count() == 0
