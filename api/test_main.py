from fastapi.testclient import TestClient
from .main import app  # Import your FastAPI instance
import os
import json

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_login_for_access_token():
    response = client.post("/token", data={"username": "johndoe", "password": "secret"})
    tokens = response.json()
    assert response.status_code == 200
    assert "access_token" in tokens
    access_token = tokens["access_token"]

    # Now use the token to access a protected endpoint
    response = client.get("/users/me", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() == {"username": "johndoe", "email": "johndoe@example.com"}
def test_read_users_me():
    access_token = test_login_for_access_token()
    response = client.get("/users/me", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() == {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "disabled": False,
    }

def test_upload_dicom():
    # You would replace 'test.dcm' with the path to an actual test DICOM file
    with open(os.path.join('tests','test.dcm'), 'rb') as f:
        response = client.post("/upload-dicom/", files={"file": ("test.dcm", f, "application/dicom")})
    assert response.status_code == 200
    assert "filename" in response.json()
    assert "tags" in response.json()


def test_extract_tags():
    with open('test.dcm', 'rb') as f:
        response = client.post("/extract-tags/", files={"file": ("test.dcm", f, "application/dicom")})
    assert response.status_code == 200
    # You would add more specific assertions here based on what tags you expect to be extracted
    assert "PatientID" in response.json()
    assert "PatientName" in response.json()
    assert "StudyDate" in response.json()

def test_modify_tags():
    access_token = test_login_for_access_token()  # Assuming this endpoint is protected
    new_tags = {"PatientID": "12345"}
    with open('test.dcm', 'rb') as f:
        response = client.post("/modify-tags/",
                               files={"file": ("test.dcm", f, "application/dicom")},
                               data={"tags": json.dumps(new_tags)},
                               headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    # You could download the file here and check that the tags have indeed been modified


def test_save_and_download():
    new_tags = {"PatientName": "Test^Patient"}
    with open('test.dcm', 'rb') as f:
        response = client.post("/save-and-download/",
                               files={"file": ("test.dcm", f, "application/dicom")},
                               data={"tags": json.dumps(new_tags)})
    assert response.status_code == 200
    # Check the response headers to ensure a file download was initiated
    assert response.headers["content-disposition"].startswith("attachment")
    assert response.headers["content-type"] == "application/octet-stream"

def test_upload_non_dicom():
    with open('not_a_dicom.txt', 'rb') as f:
        response = client.post("/upload-dicom/", files={"file": ("not_a_dicom.txt", f, "application/dicom")})
    assert response.status_code == 400
    assert "detail" in response.json()


from unittest.mock import patch

@patch('main.authenticate_user')
def test_login_with_mock(authenticate_mock):
    authenticate_mock.return_value = {"username": "johndoe"}
    response = client.post("/token", data={"username": "johndoe", "password": "secret"})
    assert response.status_code == 200
    assert "access_token" in response.json()