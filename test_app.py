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
            cursor.execute("DELETE FROM project_software")  
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

def test_delete_project_with_association(client):
    """Deletion of project with associated software."""

    client.post("/projects", json={"code": "project1", "archived": 0, "start_date": "2025-01-01", "end_date": "2025-12-31"})
    client.post("/software", json={"name": "software1", "version": "1.0.0", "vendor": "MyCompany", "deprecated": 0})

    data = {
        "code": "project1",
        "software_name": "software1",
        "version": "1.0.0"
    }

    # Associate software with project
    client.post("/projects/software", json=data)

    # Delete the project
    response = client.delete("/projects/project1")
    assert response.status_code == 400
    assert response.json == {"error": "Cannot delete project. It is associated with software."}


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

def test_delete_software_with_association(client):
    """Deletion of software with associated project."""

    client.post("/projects", json={"code": "project1", "archived": 0, "start_date": "2025-01-01", "end_date": "2025-12-31"})
    client.post("/software", json={"name": "software1", "version": "1.0.0", "vendor": "MyCompany", "deprecated": 0})

    data = {
        "code": "project1",
        "software_name": "software1",
        "version": "1.0.0"
    }

    # Associate software with project
    client.post("/projects/software", json=data)

    # Delete the software
    response = client.delete("/software/software1/1.0.0")
    assert response.status_code == 400
    assert response.json == {"error": "Cannot delete software. It is associated with a project."}


# --------------- Test Cases for Project Filter API ----------------
def test_fetch_all_projects(client):
    """fetching all projects with default pagination."""
    client.post("/projects", json={"code": "mycode"})
    response = client.get("/projects")
    assert response.status_code == 200
    data = response.get_json()
    assert "projects" in data
    assert isinstance(data["projects"], list)

def test_fetch_projects_with_pagination(client):
    """fetching projects with custom pagination."""
    client.post("/projects", json={"code": "mycode"})
    client.post("/projects", json={"code": "mycode1"})
    client.post("/projects", json={"code": "mycode2"})
    response = client.get("/projects?page=2&size=2")
    assert response.status_code == 200
    data = response.get_json()
    assert "projects" in data
    assert data["page"] == 2
    assert data["size"] <= 5

def test_fetch_projects_filtered_by_code(client):
    """fetching projects by partial code match."""
    client.post("/projects", json={"code": "mycode"})
    client.post("/projects", json={"code": "myproject"})
    response = client.get("/projects?code=proj")
    assert response.status_code == 200
    data = response.get_json()
    for project in data["projects"]:
        assert "proj" in project["code"]

def test_fetch_archived_projects(client):
    """fetching only archived projects."""
    client.post("/projects", json={"code": "mycode","archived": 1})
    client.post("/projects", json={"code": "mycode1","archived": 1})
    client.post("/projects", json={"code": "mycode2","archived": 0})
    response = client.get("/projects?archived=1")
    assert response.status_code == 200
    data = response.get_json()
    for project in data["projects"]:
        assert project["archived"] == 1

def test_fetch_projects_by_start_date(client):
    """fetching projects starting on or after a given date."""
    client.post("/projects", json={"code": "mycode","start_date": "2024-01-01"})
    client.post("/projects", json={"code": "mycode","start_date": "2025-02-01"})
    response = client.get("/projects?start_date=2025-01-01")
    assert response.status_code == 200
    data = response.get_json()
    for project in data["projects"]:
        assert project["start_date"] >= "2025-01-01"

def test_fetch_projects_by_end_date(client):
    """fetching projects ending on or before a given date."""
    client.post("/projects", json={"code": "mycode","end_date": "2026-01-01"})
    client.post("/projects", json={"code": "mycode","end_date": "2025-02-01"})
    response = client.get("/projects?end_date=2025-12-31")
    assert response.status_code == 200
    data = response.get_json()
    for project in data["projects"]:
        assert project["end_date"] is None or project["end_date"] <= "2025-12-31"

def test_fetch_projects_with_invalid_page(client):
    """handling invalid page values."""
    response = client.get("/projects?page=-1&size=abc")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Invalid page or size parameter. Must be positive integers."

def test_fetch_projects_with_special_chars(client):
    """projects retrieval with special characters in the code."""
    client.post("/projects", json={"code": "mycode","start_date": "2024-01-01"})
    client.post("/projects", json={"code": "my%$@!code","start_date": "2025-02-01"})
    response = client.get("/projects?code=%$@!")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data["projects"], list)

def test_fetch_empty_database(client):
    """fetching projects when database is empty."""
    response = client.get("/projects")
    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] == 0
    assert data["projects"] == []

def test_fetch_large_pagination(client):
    """large pagination requests."""
    client.post("/projects", json={"code": "mycode","start_date": "2024-01-01"})
    client.post("/projects", json={"code": "mycode2","start_date": "2025-02-01"})    
    response = client.get("/projects?size=1000")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["projects"]) <= 1000

def test_fetch_projects_with_all_filters(client):
    """applying multiple filters together."""
    response = client.get("/projects?code=test&archived=0&start_date=2025-01-01&end_date=2025-12-31&page=1&size=3")
    assert response.status_code == 200
    data = response.get_json()
    for project in data["projects"]:
        assert "test" in project["code"]
        assert project["archived"] == 0
        assert project["start_date"] >= "2025-01-01"
        assert project["end_date"] is None or project["end_date"] <= "2025-12-31"

# ----------------- Test Cases for associate_software_with_project API -----------------
def test_associate_software_with_project_success(client):
    """Associating a valid software with a project."""
    # First, create a project and software
    client.post("/projects", json={"code": "project1", "archived": 0, "start_date": "2025-01-01", "end_date": "2025-12-31"})
    client.post("/software", json={"name": "software1", "version": "1.0.0", "vendor": "MyCompany", "deprecated": 0})
    
    data = {
        "code": "project1",
        "software_name": "software1",
        "version": "1.0.0"
    }
    response = client.post("/projects/software", json=data)
    assert response.status_code == 201
    assert b"Software successfully associated with project" in response.data

def test_missing_code(client):
    """Missing 'code' field in request."""
    data = {
        "software_name": "software1",
        "version": "1.0.0"
    }
    response = client.post("/projects/software", json=data)
    assert response.status_code == 400
    assert response.json == {"error": "code is required"}

def test_missing_software_name(client):
    """Missing 'software_name' field in request."""
    data = {
        "code": "project1",
        "version": "1.0.0"
    }
    response = client.post("/projects/software", json=data)
    assert response.status_code == 400
    assert response.json == {"error": "software_name is required"}

def test_missing_version(client):
    """Missing 'version' field in request."""
    data = {
        "code": "project1",
        "software_name": "software1"
    }
    response = client.post("/projects/software", json=data)
    assert response.status_code == 400
    assert response.json == {"error": "version is required"}

def test_project_not_found(client):
    """Project is not found."""
    data = {
        "code": "project1",
        "software_name": "software1",
        "version": "1.0.0"
    }
    response = client.post("/projects/software", json=data)
    assert response.status_code == 404
    assert response.json == {"error": "Project not found"}

def test_software_not_found(client):
    """Software is not found."""
    client.post("/projects", json={"code": "project1", "archived": 0, "start_date": "2025-01-01", "end_date": "2025-12-31"})
    
    data = {
        "code": "project1",
        "software_name": "software1",
        "version": "1.0.0"
    }
    response = client.post("/projects/software", json=data)
    assert response.status_code == 404
    assert response.json == {"error": "Software not found"}

def test_deprecated_software(client):
    """Software is deprecated."""
    client.post("/projects", json={"code": "project1", "archived": 0, "start_date": "2025-01-01", "end_date": "2025-12-31"})
    client.post("/software", json={"name": "software1", "version": "1.0.0", "vendor": "MyCompany", "deprecated": 1})
    
    data = {
        "code": "project1",
        "software_name": "software1",
        "version": "1.0.0"
    }
    response = client.post("/projects/software", json=data)
    assert response.status_code == 400
    assert response.json == {"error": "Cannot associate a deprecated software version"}

def test_associate_with_different_major_version(client):
    """Project already has a different major version of the same software."""
    client.post("/projects", json={"code": "project1", "archived": 0, "start_date": "2025-01-01", "end_date": "2025-12-31"})
    client.post("/software", json={"name": "software1", "version": "2.0.0", "vendor": "MyCompany", "deprecated": 0})
    client.post("/software", json={"name": "software1", "version": "1.0.0", "vendor": "MyCompany", "deprecated": 0})

    # Associate software version 2.0.0
    data = {
        "code": "project1",
        "software_name": "software1",
        "version": "2.0.0"
    }
    client.post("/projects/software", json=data)

    # Now, try to associate with a different major version (1.x.x)
    data = {
        "code": "project1",
        "software_name": "software1",
        "version": "1.0.0"
    }
    response = client.post("/projects/software", json=data)
    assert response.status_code == 400
    assert response.json == {"error": "Project already uses a different major version: 2.0.0"}

def test_associate_software_with_project_duplicate_entry(client):
    """A project already has the same software version associated."""

    client.post("/projects", json={"code": "project1", "archived": 0, "start_date": "2025-01-01", "end_date": "2025-12-31"})
    client.post("/software", json={"name": "software1", "version": "1.0.0", "vendor": "MyCompany", "deprecated": 0})

    data = {
        "code": "project1",
        "software_name": "software1",
        "version": "1.0.0"
    }
    
    # First attempt to associate software
    response = client.post("/projects/software", json=data)
    assert response.status_code == 201
    assert b"Software successfully associated with project" in response.data
    
    # Now, try to associate the same software again, which should cause a duplicate error
    response = client.post("/projects/software", json=data)
    assert response.status_code == 400
    assert response.json == {"error": "Software version already associated with the project"}

