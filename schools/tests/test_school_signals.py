"""Testa que School herda campos do BaseModel do django_base_kit."""

import uuid

import pytest
from django_base_kit.models import User

from schools.models import School


@pytest.mark.django_db
def test_school_inherits_basemodel_fields():
    user = User.objects.create_user(username="owner3", email="owner3@test.com", password="p")
    school = School.objects.create(owner=user, name="Escola Três")

    # UUID primary key (do BaseModel)
    assert isinstance(school.id, uuid.UUID)

    # created_at e updated_at (do BaseModel)
    assert school.created_at is not None
    assert school.updated_at is not None

    # active (do BaseModel)
    assert school.active is True
