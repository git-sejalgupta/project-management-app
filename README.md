## Instructions for Running Flask App with Docker
### Prerequisites
Ensure you have the following installed on your machine:
- Docker

### Steps to Build and Run the Flask App
1. Clone the Repository
```
git clone <your-repository-url>
cd project-management-app
```
2. Build the Docker Image
In the project folder, run the following command to build the Docker image:
```
docker build -t flask-app .
```
3. Run the Flask App Using Docker Compose
Run the following command to start the Flask app:
```
docker-compose up
```
4. Verify the Application is Running
```
http://localhost:5000
```
### Running Tests
To run tests inside the Docker container, follow these steps:
1. Start the container using the following command (if it's not already running):
```
docker-compose up
```
2. Run the tests using the following command (in a new terminal):
```
docker-compose exec flask-app pytest test_app.py
```

## Project CRUD APIs
## API Endpoints Documentation
### CRUD APIs for Projects
1. Create Project
- Endpoint: ``` POST /projects ```
- Description: Creates a new project.
- Request Body:
  ```
  {
    "code": "PROJECT123",
    "archived": 0,
    "start_date": "2025-01-01",
    "end_date": "2025-12-31"
  }
  ```
- Response:
  - 201 Created:
    ```
    {
      "message": "Project created successfully",
      "id": 1
    }
    ```
  - 400 Bad Request (if code is missing or duplicate):

2. Get Project by Code
- Endpoint: ``` GET /projects/<code> ```
- Description: Retrieves a project by its unique code.
- Response:
  - 200 OK: 
    ```
    {
      "code": "PROJECT123",
      "archived": 0,
      "start_date": "2025-01-01",
      "end_date": "2025-12-31"
    }
    ```
  - 404 Not Found
3. Get Projects (Paginated and Filtered)
- Endpoint: ``` GET /projects ```
- Description: Retrieves a list of projects with optional filters and pagination.
- Query Parameters:
   - code: Filter by project code (optional)
   - archived: Filter by archived status (optional)
   - start_date: Filter projects starting after this date (optional)
   - end_date: Filter projects ending before this date (optional)
   - page: Page number (default: 1)
   - size: Number of results per page (default: 10)
- Response:
  - 200 OK:
    ```
      {
        "projects": [
          {
            "code": "PROJECT123",
            "archived": 0,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31"
          }
        ],
        "total": 1,
        "page": 1,
        "size": 1
      }
    ```
  - 400 Bad Request (if invalid page/size)
4. Update Project
- Endpoint: ``` PUT /projects/<code> ```
- Description: Updates a project by its unique code.
- Request Body:
  ```
  {
    "archived": 1,
    "start_date": "2025-02-01"
  }
  ```
- Response:
  - 200 OK
  - 400 Bad Request (if no valid fields to update)
5. Delete Project
- Endpoint: ``` DELETE /projects/<code> ```
- Description: Deletes a project by its unique code.
- Response:
  - 200 OK
  - 400 Not Found
### CRUD APIs for Software
1. Create Software
 - Endpoint:``` POST /software ```
- Description: Creates a new software record.
- Request Body:
  ```
    {
    "name": "SoftwareA",
    "version": "1.0.0",
    "vendor": "VendorA",
    "deprecated": 0
  }

  ```
- Response:
  - 201 Created:
    ```
    {
      "message": "Software created successfully",
      "id": 1
    }
    ```
  - 400 Bad Request (if code is missing or duplicate)
2. Get Software by Name
- Endpoint: ``` GET /software/<name> ```
- Description: Retrieves software details by its name.
- Response:
  - 200 OK
    ```
    {
      "software": [
        {
          "name": "SoftwareA",
          "version": "1.0.0",
          "vendor": "VendorA",
          "deprecated": 0
        }
      ],
      "total": 1
    }
    ```
  - 404 Not Found
3. Update Software
- Endpoint: ``` PUT /software/<name>/<version> ```
- Description: Updates software details by its name and version.
- Request Body:
  ```
    {
      "vendor": "VendorB",
      "deprecated": 1
    }
  ```
- Response:
  - 200 OK
  - 404 Not Found
4. Delete Software
- Endpoint: ``` DELETE /software/<name>/<version> ```
- Description: Deletes software by its name and version.
- Response:
  - 200 OK
  - 404 Not Found
 
### Associate Software with Project
- Endpoint: ``` POST /projects/software ```
- Description: Associates a software version with a project.
- Request Body:
  ```
  {
    "code": "PROJECT123",
    "software_name": "SoftwareA",
    "version": "1.0.0"
  }
  ```
- Response:
  - 201 Created:
  ```
    {
      "message": "Software successfully associated with project"
    }
  ```
  - 400 Bad Request (if project or software not found)
