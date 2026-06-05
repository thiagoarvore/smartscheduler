import pytest


@pytest.fixture
def user_password():
    return "testpass12345"


@pytest.fixture
def user_email():
    return "test@gradecerta.com"
