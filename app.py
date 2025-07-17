from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psycopg2
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_CONFIG = {
    "database": "paper_portal_db",
    "user": "postgres",
    "password": "Venkat@19",
    "host": "localhost",
    "port": "5432"
}

# Upload paper
@app.route("/add-paper", methods=["POST"])
def add_paper():
    try:
        title = request.form.get("title")
        subject = request.form.get("subject")
        year = request.form.get("year")
        file = request.files.get("file")

        print("Received:", title, subject, year, file.filename if file else "No file")

        if not title or not subject or not year or not file or file.filename == "":
            return jsonify({"message": "Missing fields!"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("INSERT INTO papers (title, subject, year, filename) VALUES (%s, %s, %s, %s)", 
                    (title, subject, year, filename))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Paper uploaded successfully!"})
    except Exception as e:
        return jsonify({"message": "Upload failed", "error": str(e)}), 500


# Get papers
@app.route("/get-papers", methods=["GET"])
def get_papers():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT id, title, subject, year, filename FROM papers")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify([{"id": r[0], "title": r[1], "subject": r[2], "year": r[3], "filename": r[4]} for r in rows])
    except Exception as e:
        return jsonify([])

# Delete paper by ID
@app.route("/delete-paper/<int:paper_id>", methods=["DELETE"])
def delete_paper(paper_id):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("SELECT filename FROM papers WHERE id = %s", (paper_id,))
        result = cur.fetchone()
        if result:
            filename = result[0]
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                os.remove(file_path)

            cur.execute("DELETE FROM papers WHERE id = %s", (paper_id,))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"message": "Paper deleted successfully!"})
        else:
            return jsonify({"message": "Paper not found"}), 404
    except Exception as e:
        return jsonify({"message": "Deletion failed", "error": str(e)}), 500

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/")
def serve_index():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    app.run(debug=True)
