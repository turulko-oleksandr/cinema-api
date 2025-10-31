import io
import pytest
from fastapi import status
from unittest.mock import AsyncMock, MagicMock

from app.routes.profiles import ALLOWED_IMAGE_TYPES, MAX_FILE_SIZE


@pytest.mark.asyncio
async def test_get_profile_creates_and_returns_profile(
    client, auth_headers, monkeypatch
):
    """Test GET /api/v1/profile/ returns or creates user profile"""
    # Mock get_minio_service to avoid real connection
    mock_minio = MagicMock()
    mock_minio.get_file_url.return_value = "http://minio.test/avatar.jpg"
    monkeypatch.setattr("app.routes.profiles.get_minio_service", lambda: mock_minio)

    response = await client.get("/api/v1/profile/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "id" in data
    assert "user_id" in data
    assert data["avatar_url"] in (None, "http://minio.test/avatar.jpg")


@pytest.mark.asyncio
async def test_update_profile_success(client, auth_headers, monkeypatch):
    """Test PUT /api/v1/profile/ updates profile successfully"""
    mock_minio = MagicMock()
    mock_minio.get_file_url.return_value = "http://minio.test/avatar.jpg"
    monkeypatch.setattr("app.routes.profiles.get_minio_service", lambda: mock_minio)

    update_data = {
        "first_name": "John",
        "last_name": "Doe",
        "gender": "MAN",
        "info": "Test user info",
    }

    response = await client.put(
        "/api/v1/profile/", json=update_data, headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["info"] == "Test user info"


@pytest.mark.asyncio
async def test_update_profile_no_fields(client, auth_headers):
    """Test PUT /api/v1/profile/ without fields returns 400"""
    response = await client.put("/api/v1/profile/", json={}, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "No fields to update"


@pytest.mark.asyncio
async def test_upload_avatar_success(client, auth_headers, monkeypatch):
    """Test POST /api/v1/profile/avatar uploads and saves avatar"""
    mock_minio = MagicMock()
    mock_minio.upload_file.return_value = "avatars/test_avatar.png"
    mock_minio.get_file_url.return_value = "http://minio.test/avatars/test_avatar.png"
    mock_minio.delete_file.return_value = True

    monkeypatch.setattr("app.routes.profiles.get_minio_service", lambda: mock_minio)

    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"a" * 1024)
    files = {"file": ("test.png", fake_image, "image/png")}

    response = await client.post(
        "/api/v1/profile/avatar", files=files, headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "avatar" in data
    assert "avatar_url" in data
    assert data["avatar_url"].startswith("http://minio.test")


@pytest.mark.asyncio
async def test_upload_avatar_invalid_type(client, auth_headers):
    """Test POST /api/v1/profile/avatar with invalid file type"""
    fake_file = io.BytesIO(b"not an image")
    files = {"file": ("bad.txt", fake_file, "text/plain")}
    response = await client.post(
        "/api/v1/profile/avatar", files=files, headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_avatar_too_large(client, auth_headers):
    """Test POST /api/v1/profile/avatar with too large file"""
    large_data = io.BytesIO(b"a" * (MAX_FILE_SIZE + 1))
    files = {"file": ("huge.png", large_data, "image/png")}
    response = await client.post(
        "/api/v1/profile/avatar", files=files, headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "File too large" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_avatar_success_full_flow(
    client, auth_headers: dict, monkeypatch, db_session
):
    MOCKED_OBJECT_NAME = "avatars/uploaded_file.png"

    mock_minio = MagicMock()

    mock_minio.upload_file.return_value = MOCKED_OBJECT_NAME
    mock_minio.get_file_url.return_value = f"http://test.minio/{MOCKED_OBJECT_NAME}"
    mock_minio.delete_file.return_value = True

    monkeypatch.setattr("app.routes.profiles.get_minio_service", lambda: mock_minio)

    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"a" * 512)
    files = {"file": ("avatar.png", fake_image, "image/png")}

    upload_resp = await client.post(
        "/api/v1/profile/avatar", files=files, headers=auth_headers
    )

    assert upload_resp.status_code == status.HTTP_201_CREATED
    mock_minio.upload_file.assert_called_once()

    delete_resp = await client.delete("/api/v1/profile/avatar", headers=auth_headers)

    assert delete_resp.status_code == status.HTTP_204_NO_CONTENT

    mock_minio.delete_file.assert_called_once_with(MOCKED_OBJECT_NAME)

    assert mock_minio.delete_file.call_count == 1
    assert mock_minio.upload_file.call_count == 1


@pytest.mark.asyncio
async def test_delete_avatar_not_found(client, auth_headers, monkeypatch):
    """Test DELETE /api/v1/profile/avatar with no avatar returns 404"""

    async def mock_delete_user_avatar(db, user_id):
        return None

    monkeypatch.setattr(
        "app.routes.profiles.delete_user_avatar", mock_delete_user_avatar
    )

    response = await client.delete("/api/v1/profile/avatar", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "No avatar to delete"
