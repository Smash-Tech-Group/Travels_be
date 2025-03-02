"""
Test for GET user statistics endpoint
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from uuid_extensions import uuid7
from fastapi import status
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.v1.models.user import User
from api.v1.services.user import user_service, UserService


client = TestClient(app)

mock_id = str(uuid7().hex)
ENDPOINT = f"/api/v1/users/{mock_id}/restore"


@pytest.fixture
def mock_db_session():
    """Fixture to create a mock database session."

    Yields:
        MagicMock: mock database
    """

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


@pytest.fixture
def mock_get_current_user():
    """Fixture to create a mock current user"""
    with patch(
        "api.v1.services.user.UserService.get_current_user", autospec=True
    ) as mock_get_current_user:
        yield mock_get_current_user


@pytest.fixture
def override_get_current_super_admin():
    """Mock the get_current_super_admin dependency"""

    app.dependency_overrides[user_service.get_current_super_admin] = lambda: User(
        id=str(uuid7().hex),
        email="admintestuser@gmail.com",
        password=user_service.hash_password("Testpassword@123"),
        first_name="AdminTest",
        last_name="User",
        is_active=False,
        is_superadmin=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


mock_users = [
    {"id": 1, "is_active": True, "is_deleted": False},
    {"id": 2, "is_active": True, "is_deleted": False},
    {"id": 3, "is_active": False, "is_deleted": False},
    {"id": 4, "is_active": False, "is_deleted": False},
    {"id": 5, "is_active": True, "is_deleted": True},
    {"id": 6, "is_active": True, "is_deleted": False},
    {"id": 7, "is_active": False, "is_deleted": True},
    {"id": 8, "is_active": True, "is_deleted": False},
    {"id": 9, "is_active": False, "is_deleted": False},
    {"id": 10, "is_active": True, "is_deleted": True},
]


@pytest.mark.usefixtures("mock_db_session", "mock_user_service")
def test_unauthorised_access(mock_user_service: UserService, mock_db_session: Session):
    """Test for unauthorized access to endpoint."""

    response = client.put(ENDPOINT)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.usefixtures(
    "mock_db_session", "mock_user_service", "mock_get_current_user"
)
def test_non_admin_access(
    mock_get_current_user, mock_user_service: UserService, mock_db_session: Session
):
    """Test for non admin user access to endpoint"""

    mock_get_current_user.return_value = User(
        id=str(uuid7().hex),
        email="admintestuser@gmail.com",
        password=user_service.hash_password("Testpassword@123"),
        first_name="AdminTest",
        last_name="User",
        is_active=False,
        is_superadmin=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    response = client.put(
        ENDPOINT,
        headers={"Authorization": "Bearer dummy_token"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.usefixtures(
    "mock_db_session", "mock_user_service", "override_get_current_super_admin"
)
def test_user_not_found(
    mock_user_service: UserService,
    mock_db_session: Session,
    override_get_current_super_admin: None,
):
    mock_db_session.get.return_value = None

    response = client.put(ENDPOINT)

    print(response.json())

    assert response.status_code == 404


@pytest.mark.usefixtures(
    "mock_db_session", "mock_user_service", "override_get_current_super_admin"
)
def test_successful_restore(
    mock_user_service: UserService,
    mock_db_session: Session,
    override_get_current_super_admin: None,
):
    response = client.put(ENDPOINT)

    assert response.status_code == 200
