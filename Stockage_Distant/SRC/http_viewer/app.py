from flask import Flask, render_template
import sqlite3

app = Flask(__name__)
DB = "app.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM images
        ORDER BY created_at DESC
        LIMIT 5
    """)
    rows = cursor.fetchall()
    conn.close()

    return render_template("index.html", images=rows)

if __name__ == "__main__":
    app.run(debug=True)
