import pytest
import os
from app import app, get_db, init_db

@pytest.fixture
def client():
    """Setup a test client with an in-memory database."""
    TEST_DB_FILE = "database/test.db"
    app.config["TESTING"] = True  # testing mode (uses test database)
    app.config["DATABASE"] = TEST_DB_FILE  

    with app.test_client() as client:
        with app.app_context():
            init_db()  # Initialize schema in test DB
        
        yield client  # Run test
        
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM projects")  
            cursor.execute("DELETE FROM software")  
            db.commit()
            db.close()

# --------------- Test Cases for Project APIs ----------------

def test_create_project(client):
    """creating a new project."""
    response = client.post("/projects", json={"code": "mycode1", "archived": 0, "start_date": "2025-01-01", "end_date": "2025-12-31"})

    assert response.status_code == 201
    assert b"Project created successfully" in response.data

def test_create_project_duplicate(client):
    """creating a project with duplicate code."""
    client.post("/projects", json={"code": "mycode2"})
    response = client.post("/projects", json={"code": "mycode2"})
    assert response.status_code == 400
    assert b"already exists" in response.data

def test_create_project_missing_code(client):
    """project creation failure due to missing code."""
    response = client.post("/projects", json={"archived": 0})
    assert response.status_code == 400
    assert b"Project code is required" in response.data

def test_get_project_by_code(client):
    """retrieving project details by code."""
    client.post("/projects", json={"code": "mycode"})
    response = client.get("/projects/mycode")
    assert response.status_code == 200
    assert b"mycode" in response.data

def test_get_project_not_found(client):
    """retrieving a project that does not exist."""
    response = client.get("/projects/myproject")
    assert response.status_code == 404
    assert b"Project not found" in response.data

def test_update_project(client):
    """updating a project."""
    client.post("/projects", json={"code": "mycode"})
    response = client.put("/projects/mycode", json={"archived": 1})
    assert response.status_code == 200
    assert b"Project updated successfully" in response.data

def test_update_project_not_found(client):
    """updating a non-existent project."""
    response = client.put("/projects/myproject", json={"archived": 1})
    assert response.status_code == 404
    assert b"Project not found" in response.data

def test_delete_project(client):
    """deleting a project."""
    client.post("/projects", json={"code": "mycode"})
    response = client.delete("/projects/mycode")
    assert response.status_code == 200
    assert b"Project deleted successfully" in response.data

def test_delete_project_not_found(client):
    """deleting a non-existent project."""
    response = client.delete("/projects/myproject")
    assert response.status_code == 404
    assert b"Project not found" in response.data

# --------------- Test Cases for Software APIs ----------------

def test_create_software(client):
    """creating a new software entry."""
    response = client.post("/software", json={"name": "Python", "version": "3.9", "vendor": "Python", "deprecated": 0})
    assert response.status_code == 201
    assert b"Software created successfully" in response.data

def test_create_software_duplicate(client):
    """creating duplicate software entry."""
    client.post("/software", json={"name": "Java", "version": "17", "vendor": "Oracle"})
    response = client.post("/software", json={"name": "Java", "version": "17", "vendor": "Oracle"})
    assert response.status_code == 400
    assert b"already exists" in response.data

def test_create_software_missing_version(client):
    """software creation failure due to missing fields."""
    response = client.post("/software", json={"name": "NodeJS"})
    assert response.status_code == 400
    assert b"version is required" in response.data

def test_get_software_by_name(client):
    """retrieving software details by name."""
    client.post("/software", json={"name": "Python", "version": "3.9", "vendor": "Python"})
    response = client.get("/software/Python")
    assert response.status_code == 200
    assert b"Python" in response.data

def test_get_software_not_found(client):
    """retrieving a software that does not exist."""
    response = client.get("/software/Rust")
    assert response.status_code == 200  # Still returns empty list
    assert b'{"software":[],"total":0}\n' in response.data

def test_update_software(client):
    """updating a software entry."""
    client.post("/software", json={"name": "Python", "version": "3.9", "vendor": "Python"})
    response = client.put("/software/Python/3.9", json={"deprecated": 1})
    assert response.status_code == 200
    assert b"Software updated successfully" in response.data

def test_update_software_not_found(client):
    """updating a non-existent software entry."""
    response = client.put("/software/Java/8", json={"deprecated": 1})
    assert response.status_code == 404
    assert b"Software not found" in response.data

def test_delete_software(client):
    """deleting a software entry."""
    client.post("/software", json={"name": "Python", "version": "3.9", "vendor": "Python"})
    response = client.delete("/software/Python/3.9")
    assert response.status_code == 200
    assert b"Software deleted successfully" in response.data

def test_delete_software_not_found(client):
    """deleting a non-existent software entry."""
    response = client.delete("/software/Python/3.9")
    assert response.status_code == 404
    assert b"Software not found" in response.data
