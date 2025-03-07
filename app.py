from flask import Flask, request, jsonify, g
import sqlite3
import logging
import os

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

DB_FILE = "database/exercise.db"
TEST_DB_FILE = "database/test.db"

def get_db():
    '''
        Returns a connection to the SQLite database.
    '''
    # Get the database connection from the Flask application context
    if "_database" not in g:
        if app.config.get("TESTING"):
            g._database = sqlite3.connect(TEST_DB_FILE)  # Use test db DB for tests
        else:
            g._database = sqlite3.connect(DB_FILE)

        g._database.row_factory = sqlite3.Row

    return g._database

def init_db():
    '''
        Initialize database and create necessary tables
    '''
    with app.app_context():
        # Gets the database connection
        db = get_db()
        # Execute the content in schema.sql file to create tables
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        
        db.commit()
        logger.debug(f"db initialization done")

# Function to run before each request
@app.before_request
def before_request():
    '''
        Ensure database connection is available
    '''
    # Get the database connection and store it in the Flask application context
    g._database = get_db()  

#Function to run after each request
@app.teardown_request
def close_connection(exception):
    '''
        to ensure the database connection is closed properly
    '''    
    # Get the database connection from the Flask application context
    db = getattr(g, '_database', None)  
    # Close the database connection if it exists
    if db is not None:
        db.close()  
        logger.debug(f"db connection closed")

# Global error handler
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request", "message": str(error)}), 400

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error", "message": "An unexpected error occurred"}), 500

# CRUD APIs for Projects
@app.route("/projects", methods=["POST"])
def create_project():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "code" not in data:
        return jsonify({"error": "Project code is required"}), 400

    db = get_db()

    cursor = db.cursor()

    try:
        cursor.execute(
            "INSERT INTO projects (code, archived, start_date, end_date) VALUES (?, ?, ?, ?)",
            (data["code"], data.get("archived", 0), data.get("start_date"), data.get("end_date")),
        )
        db.commit()
        
        project_id = cursor.lastrowid
        logger.info(f"Project created: {data['code']} (ID: {project_id})") 
        return jsonify({"message": "Project created successfully", "id": project_id}), 201

    except sqlite3.IntegrityError:
        logger.warning(f"Project creation failed: Code {data['code']} already exists")
        return jsonify({"error": f"Project with code {data['code']} already exists"}), 400
    except sqlite3.Error as e:
        logger.error(f"Database error during project creation: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route("/projects/<string:code>", methods=["GET"])
def get_project_by_code(code):
    logger.info(f"Searching projects by code: {code}")

    db = get_db()
    cursor = db.cursor()
    
    query = "SELECT code, archived, start_date, end_date FROM projects WHERE code = ?"

    cursor.execute(query, (code,))
    project = cursor.fetchone()

    if project is None:
        return jsonify({"error": "Project not found"}), 404

    # Convert row to dictionary
    project_dict = dict(zip([column[0] for column in cursor.description], project))

    return jsonify(project_dict)

# Filter projects and serves paginated results
@app.route("/projects", methods=["GET"])
def get_projects():
    db = get_db()
    cursor = db.cursor()

    # Get filters from request
    code = request.args.get("code")
    archived = request.args.get("archived")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # Pagination with default   
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", 10))
        if page < 1 or size < 1:
            raise ValueError
    except ValueError:
        return jsonify({"error": "Invalid page or size parameter. Must be positive integers."}), 400

    offset = (page - 1) * size
    # Base query
    base_query = " FROM projects WHERE 1=1"
    params = []

    # filters
    if code:
        base_query += " AND code LIKE ?"
        params.append(f"%{code}%")
    
    if archived is not None:
        base_query += " AND archived = ?"
        params.append(int(archived))

    if start_date:
        base_query += " AND start_date >= ?"
        params.append(start_date)

    if end_date:
        base_query += " AND end_date <= ?"
        params.append(end_date)

    # Query to get paginated results
    query = "SELECT *" + base_query + " LIMIT ? OFFSET ?"
    params.extend([size, offset])

    cursor.execute(query, params)
    projects = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    
    # Query to get total count
    count_query = "SELECT COUNT(*)" + base_query
    cursor.execute(count_query, params[:-2])  # removing LIMIT/OFFSET
    total_count = cursor.fetchone()[0]

    return jsonify({
        "projects": projects,
        "total": total_count,
        "page": page,
        "size": len(projects)
    })

@app.route("/projects/<code>", methods=["PUT"])
def update_project(code):
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    db = get_db()
    cursor = db.cursor()

    fields = []
    values = []

    if "archived" in data:
        fields.append("archived = ?")
        values.append(data["archived"])

    if "start_date" in data:
        fields.append("start_date = ?")
        values.append(data["start_date"])

    if "end_date" in data:
        fields.append("end_date = ?")
        values.append(data["end_date"])

    if not fields:
        return jsonify({"error": "No valid fields to update"}), 400

    values.append(code)
    query = f"UPDATE projects SET {', '.join(fields)} WHERE code = ?"

    try:
        cursor.execute(query, values)
        db.commit()

        if cursor.rowcount == 0:
            logger.warning(f"Project update failed: Code {code} not found") 
            return jsonify({"error": "Project not found"}), 404

        logger.info(f"Project with code updated: {code}")  
        return jsonify({"message": "Project updated successfully"})
    
    except sqlite3.Error as e:
        logger.error(f"Database error during project updation: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/projects/<string:code>", methods=["DELETE"])
def delete_project(code):
    db = get_db()
    cursor = db.cursor()

    try:
        # Check if the project is associated with any software
        cursor.execute("SELECT 1 FROM project_software WHERE project_id = (SELECT id FROM projects WHERE code = ?)", (code,))
        association = cursor.fetchone()

        if association:
            logger.warning(f"Cannot delete project {code}: It has associated software.")
            return jsonify({"error": "Cannot delete project. It is associated with software."}), 400
                
        cursor.execute("DELETE FROM projects WHERE code = ?", (code,))
        db.commit()

        if cursor.rowcount == 0:
            logger.warning(f"Project deletion failed: Code {code} not found")
            return jsonify({"error": "Project not found"}), 404

        logger.info(f"Project with code deleted: {code}") 
        return jsonify({"message": "Project deleted successfully"})
    
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    
# CRUD APIs for Software
@app.route("/software", methods=["POST"])
def create_software():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "name" not in data:
        return jsonify({"error": "name is required"}), 400

    if "version" not in data:
        return jsonify({"error": "version is required"}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            "INSERT INTO software (name, version, vendor, deprecated) VALUES (?, ?, ?, ?)",
            (data["name"], data["version"], data["vendor"], data.get("deprecated", 0)),
        )
        db.commit()
        
        software_id = cursor.lastrowid
        logger.info(f"Software: {data['name']} with version: {data['version']} created (ID: {software_id})") 
        return jsonify({"message": "Software created successfully", "id": software_id}), 201

    except sqlite3.IntegrityError:
        logger.warning(f"Software creation failed: Software: {data['name']} with version: {data['version']} already exists")
        return jsonify({"error": f"Software: {data['name']} with version: {data['version']} already exists"}), 400
    except sqlite3.Error as e:
        logger.error(f"Database error during software creation: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route("/software/<string:name>", methods=["GET"])
def get_software_by_name(name):
    logger.info(f"Searching software by name: {name}")

    db = get_db()
    cursor = db.cursor()
    
    query = "SELECT name, version, vendor, deprecated FROM software WHERE name = ?"

    cursor.execute(query, (name,))
    software = [dict(row) for row in cursor.fetchall()]

    if software is None:
        return jsonify({"error": "Software not found"}), 404

    return jsonify({"software": software, "total": len(software)})

@app.route("/software/<string:name>/<string:version>", methods=["PUT"])
def update_software(name, version):
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    db = get_db()
    cursor = db.cursor()

    fields = []
    values = []

    if "vendor" in data:
        fields.append("vendor = ?")
        values.append(data["vendor"])

    if "deprecated" in data:
        fields.append("deprecated = ?")
        values.append(int(data["deprecated"]))

    if not fields:
        return jsonify({"error": "No valid fields to update"}), 400

    values.append(name)
    values.append(version)
    query = f"UPDATE software SET {', '.join(fields)} WHERE name = ? AND version = ?"

    try:
        cursor.execute(query, values)
        db.commit()

        if cursor.rowcount == 0:
            logger.warning(f"Software update failed: software {name} with version {version} not found") 
            return jsonify({"error": "Software not found"}), 404

        logger.info(f"Software with software {name} with version {version} updated")  
        return jsonify({"message": "Software updated successfully"})
    
    except sqlite3.Error as e:
        logger.error(f"Database error during software updation: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/software/<string:name>/<string:version>", methods=["DELETE"])
def delete_software(name, version):
    db = get_db()
    cursor = db.cursor()

    try:
        # Check if the software is associated with any project
        cursor.execute("""
            SELECT 1 FROM project_software 
            WHERE software_id = (SELECT id FROM software WHERE name = ? AND version = ?)
        """, (name, version))
        association = cursor.fetchone()

        if association:
            logger.warning(f"Cannot delete software {name} v{version}: It is associated with a project.")
            return jsonify({"error": "Cannot delete software. It is associated with a project."}), 400

        cursor.execute("DELETE FROM software WHERE name = ? AND version = ?", (name, version))
        db.commit()

        if cursor.rowcount == 0:
            logger.warning(f"Software deletion failed: {name} v{version} not found")
            return jsonify({"error": "Software not found"}), 404

        logger.info(f"Software deleted: {name} v{version}") 
        return jsonify({"message": "Software deleted successfully"})
    
    except sqlite3.Error as e:
        logger.error(f"Database error during Software deletion: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# An endpoint that associates a software version with a project
@app.route('/projects/software', methods=['POST'])
def associate_software_with_project():
    data = request.get_json()
    code = data.get('code')
    software_name = data.get('software_name')
    version = data.get('version')

    if not code:
        logging.warning(f"Missing required fields: code")
        return jsonify({'error': 'code is required'}), 400

    if not software_name:
        logging.warning(f"Missing required fields: software_name")
        return jsonify({'error': 'software_name is required'}), 400
    
    if not version:
        logging.warning(f"Missing required fields: version")
        return jsonify({'error': 'version is required'}), 400

    # Extract major version
    major_version = version.split('.')[0]

    db = get_db()
    cursor = db.cursor()

    try:
        # Fetch project ID from project name
        cursor.execute("SELECT id FROM projects WHERE code = ?", (code,))
        project = cursor.fetchone()

        if not project:
            logging.warning(f"Project {code} not found")
            return jsonify({'error': 'Project not found'}), 404

        project_id = project['id']

        # Fetch software info
        cursor.execute("SELECT id, deprecated FROM software WHERE name = ? AND version = ?", (software_name, version))
        software = cursor.fetchone()

        if not software:
            logging.warning(f"Software {software_name} version {version} not found")
            return jsonify({'error': 'Software not found'}), 404

        if software['deprecated']:
            logging.warning(f"Attempt to associate deprecated software {software_name} version {version}")
            return jsonify({'error': 'Cannot associate a deprecated software version'}), 400

        # Check if the project already has the same software version associated
        cursor.execute("""
            SELECT 1 
            FROM project_software 
            WHERE project_id = ? AND software_id = ?
        """, (project_id, software['id']))

        if cursor.fetchone():
            logging.warning(f"Project {project_id} already has {software_name} version {version} associated")
            return jsonify({'error': 'Software version already associated with the project'}), 400

        # Check if project already has a different major version of the software
        cursor.execute("""
            SELECT s.version 
            FROM software s
            JOIN project_software ps 
            ON s.id = ps.software_id
            WHERE s.deprecated = 0 AND ps.project_id = ? AND s.name = ?
        """, (project_id, software_name))

        existing_versions = cursor.fetchall()

        for row in existing_versions:
            existing_major_version = row['version'].split('.')[0]

            if existing_major_version != major_version:
                logging.warning(f"Project {project_id} already uses a different major version: {row['version']}")
                return jsonify({'error': f'Project already uses a different major version: {row["version"]}'}), 400

        # Associate software with project
        cursor.execute("INSERT INTO project_software (project_id, software_id) VALUES (?, ?)", (project_id, software['id']))
        db.commit()

        logging.info(f"Software {software_name} version {version} associated with project {project_id}")
        return jsonify({'message': 'Software successfully associated with project'}), 201

    except sqlite3.IntegrityError:
        logger.warning(f"Project creation failed: Code {data['code']} with software {data['software_name']} and version {data['version']} already exists")
        return jsonify({"error": f"Project with code and version already exists"}), 400

    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500


if __name__ == "__main__":
    init_db()
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=5000, debug=True)