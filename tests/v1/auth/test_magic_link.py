import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from api.v1.models.user import User
from api.v1.services.user import user_service
from uuid_extensions import uuid7
from api.db.database import get_db
from fastapi import status
from datetime import datetime, timezone
import smtplib

client = TestClient(app)
MAGIC_ENDPOINT = '/api/v1/auth/magic-link'


@pytest.fixture
def mock_db_session():
    """Fixture to create a mock database session."""

    with patch("api.v1.services.user.get_db", autospec=True) as mock_get_db:
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        yield mock_db
    app.dependency_overrides = {}


@pytest.fixture
def mock_user_service():
    """Fixture to create a mock user service."""

    with patch("api.v1.services.user.user_service", autospec=True) as mock_service:
        yield mock_service


def test_request_magic_link(mock_user_service, mock_db_session, mock_send_email):
    """Test for requesting magic link"""

    # Create a mock user
    mock_user = User(
        id=str(uuid7().hex),
        email="testuser1@gmail.com",
        password=user_service.hash_password("Testpassword@123"),
        first_name='Test',
        last_name='User',
        is_active=False,
        is_superadmin=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user

    # Test for requesting magic link for an existing user
    magic_login = client.post(MAGIC_ENDPOINT, json={
        "user_email": mock_user.email
    })
    assert magic_login.status_code == status.HTTP_200_OK
