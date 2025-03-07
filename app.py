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

if __name__ == "__main__":
    init_db()
    app.run(debug=True)