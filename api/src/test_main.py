from pathlib import Path
import time
import pytest
from fastapi.testclient import TestClient
from src.main import app, hoogle_root_dir

client = TestClient(app)

@pytest.fixture
def setup_user_folder():
    """Fixture to set up a test user folder."""
    test_user = "user"

    res = client.post("/token", data={"username": test_user, "password": "user"})
    user_token = res.json().get("access_token")
    print(user_token)

    user_folder = hoogle_root_dir / test_user
    if not user_folder.exists():
        user_folder.mkdir()
    print(user_folder)

    yield user_token

    if user_folder.exists():
        for item in user_folder.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                item.rmdir()
        user_folder.rmdir()

def test_create_folder_success(setup_user_folder):
    """Test successful folder creation."""
    test_user = setup_user_folder
    user_folder = "user"
    response = client.post(
        "/folder?path=/&folder_name=new_folder",
        headers={"Authorization": f"Bearer {test_user}"}
    )
    assert (hoogle_root_dir / user_folder / "new_folder").exists()
    assert response.status_code == 201

def test_create_folder_invalid_path(setup_user_folder):
    """Test folder creation with invalid path traversal."""
    test_user = setup_user_folder
    response = client.post(
        "/folder?path=../outside&folder_name=new_folder",
        headers={"Authorization": f"Bearer {test_user}"}
    )
    assert response.json() == {"error": "Invalid path: Path traversal detected"}
    assert response.status_code == 400

def test_create_folder_already_exists(setup_user_folder):
    """Test folder creation when the folder already exists."""
    test_user = setup_user_folder
    user_folder = "user"
    existing_folder = hoogle_root_dir / user_folder / "existing_folder"
    existing_folder.mkdir()
    response = client.post(
        "/folder?path=/&folder_name=existing_folder",
        headers={"Authorization": f"Bearer {test_user}"}
    )
    assert response.status_code == 400
    assert response.json() == {"error": "Folder 'existing_folder' already exists in '/'"}

def test_upload_file_success(setup_user_folder):
    """Test successful file upload."""
    test_user = setup_user_folder
    user_folder = "user"
    file_path = hoogle_root_dir / user_folder / "test_file.txt"
    with open("test_file.txt", "w") as f:
        f.write("Test content")
    with open("test_file.txt", "rb") as f:
        response = client.post(
            "/upload?path=/&force=false",
            files={"file": ("test_file.txt", f)},
            headers={"Authorization": f"Bearer {test_user}"}
        )
    
    Path("test_file.txt").unlink()  # Clean up test file
    assert response.status_code == 201
    assert (hoogle_root_dir / user_folder / "test_file.txt").exists()

def test_download_file_success(setup_user_folder):
    """Test successful file download."""
    test_user = setup_user_folder
    user_folder = "user"
    file_path = hoogle_root_dir / user_folder / "test_file.txt"
    with open(file_path, "w") as f:
        f.write("Test content")
    
    response = client.get(
        f"/file?path=/test_file.txt",
        headers={"Authorization": f"Bearer {test_user}"}
    )

    assert response.status_code == 200
    assert response.content == b"Test content"
    
    file_path.unlink()  # Clean up test file

def test_list_dir(setup_user_folder):
    """Test listing directory contents."""
    test_user = setup_user_folder
    user_folder = "user"
    dir_path = hoogle_root_dir / user_folder / "test_dir"
    dir_path.mkdir(exist_ok=True)
    
    response = client.get(
        f"/list_dir?path=/test_dir",
        headers={"Authorization": f"Bearer {test_user}"}
    )
    
    assert response.status_code == 200
    assert response.json() == {"files": []}
    
    dir_path.rmdir()  # Clean up test directory

def test_delete_file_success(setup_user_folder):
    """Test successful file deletion."""
    test_user = setup_user_folder
    user_folder = "user"
    file_path = hoogle_root_dir / user_folder / "test_file.txt"
    with open(file_path, "w") as f:
        f.write("Test content")
    
    response = client.delete(
        f"/file?path=/test_file.txt",
        headers={"Authorization": f"Bearer {test_user}"}
    )
    
    assert response.status_code == 204
    assert not file_path.exists()  # Ensure the file is deleted