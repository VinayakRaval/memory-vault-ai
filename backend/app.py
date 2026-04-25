from flask import Flask, request, jsonify, render_template, send_file
from database import get_db
from scanner import scan_folder
from analyzer import calculate_importance
from viewer import read_file
from threading import Thread
import os

app = Flask(__name__)

progress = {
    "total": 0,
    "current": 0,
    "status": "Idle",
    "current_folder": "",
    "paused": False,
    "stop": False,
}

# ================= HOME =================
@app.route("/")
def home():
    return render_template("index.html")

# ================= BACKGROUND SCAN =================
def background_scan(folder_path):
    files = scan_folder(folder_path, progress)

    db = get_db()
    cursor = db.cursor()

    for file in files:
        if progress.get("stop"):
            break

        # skip already scanned path
        cursor.execute("SELECT id FROM files WHERE path=%s", (file["path"],))
        if cursor.fetchone():
            continue

        importance, _ = calculate_importance(file["path"], file["name"])

        # 🔥 FORCE HASH (CRITICAL FIX)
        file_hash = file.get("hash")
        if not file_hash:
            from scanner import get_file_hash
            file_hash = get_file_hash(file["path"])

        cursor.execute("""
            INSERT INTO files 
            (name, path, type, importance, views, file_hash, size, preview, malware, malware_reason)
            VALUES (%s,%s,%s,%s,0,%s,%s,%s,%s,%s)
        """, (
            file["name"],
            file["path"],
            file["type"],
            importance,
            file_hash,
            file.get("size"),
            file.get("preview"),
            file.get("malware", 0),
            file.get("malware_reason")
        ))

    db.commit()
    cursor.close()
    db.close()
    progress["status"] = "Completed"

# ================= START SCAN =================
import time
from flask import jsonify

@app.route("/scan", methods=["POST"])
def scan():
    folder_path = request.json.get("path")

    progress["paused"] = False
    progress["stop"] = False
    progress["status"] = "Scanning"
    progress["start_time"] = time.time()

    Thread(target=background_scan, args=(folder_path,)).start()

    return {"message": "Scan started"}

@app.route("/progress")
def get_progress():
    percent = 0
    speed = 0
    eta = 0

    total = progress.get("total", 0)
    current = progress.get("current", 0)

    if total > 0:
        percent = int((current / total) * 100)

    # 🔥 SAFE SPEED CALCULATION
    if progress.get("start_time") and current > 0:
        elapsed = time.time() - progress["start_time"]

        if elapsed > 1:  # avoid unstable early values
            speed = current / elapsed

            remaining = total - current

            if speed > 0:
                eta = remaining / speed

    return jsonify({
        "percent": percent,
        "status": progress.get("status"),
        "current": current,
        "total": total,
        "speed": round(speed, 2),
        "eta": int(eta),
        "folder": progress.get("current_folder"),
        "file": progress.get("current_file")   # ✅ ADD THIS
    })
# ================= FILES =================
@app.route("/files")
def get_files():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM files ORDER BY id DESC")
    data = cursor.fetchall()

    cursor.close()
    db.close()
    return jsonify(data)

# ================= FILE STREAM (FIX DOWNLOAD ISSUE) =================
@app.route("/file")
def serve_file():
    path = request.args.get("path")

    if not path or not os.path.exists(path):
        return "File not found", 404

    return send_file(path, as_attachment=False)  # 🔥 FIX

# ================= OPEN FILE =================
from datetime import datetime

@app.route("/open/<int:file_id>")
def open_file(file_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM files WHERE id=%s", (file_id,))
    file = cursor.fetchone()

    if not file:
        return {"error": "File not found"}

    # 🔥 UPDATE BEHAVIOR
    cursor.execute("""
        UPDATE files
        SET open_count = open_count + 1,
            last_opened = %s
        WHERE id=%s
    """, (datetime.now(), file_id))

    db.commit()

    content = read_file(file["path"])

    cursor.close()
    db.close()

    return {
        "name": file["name"],
        "path": file["path"],
        "type": content.get("type"),
        "content": content.get("content")
    }
    
    
# ================= RECENT =================
@app.route("/recent")
def recent():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM files
        WHERE last_opened IS NOT NULL
        ORDER BY last_opened DESC
        LIMIT 200
    """)

    data = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(data)

# ================= DUPLICATES =================
@app.route("/duplicates")
def duplicates():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT file_hash, COUNT(*) as copies, MIN(name) as name
        FROM files
        WHERE file_hash IS NOT NULL AND file_hash != ''
        GROUP BY file_hash
        HAVING copies > 1
    """)

    rows = cursor.fetchall()

    result = []
    for r in rows:
        result.append({
            "name": r["name"],
            "copies": r["copies"],
            "hash": r["file_hash"],
            "reason": "Same content (hash match)"
        })

    cursor.close()
    db.close()
    return jsonify(result)

# ================= CLEAN DUPLICATES =================
@app.route("/clean-duplicates/<file_hash>", methods=["DELETE"])
def clean_duplicates(file_hash):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, path, importance, views
        FROM files
        WHERE file_hash=%s
        ORDER BY importance DESC, views DESC
    """, (file_hash,))

    files = cursor.fetchall()

    if len(files) <= 1:
        return {"message": "No duplicates"}

    keep_file = files[0]

    deleted = 0

    for f in files[1:]:
        try:
            if os.path.exists(f["path"]):
                os.remove(f["path"])   # ✅ REAL DELETE
        except:
            pass

        cursor.execute("DELETE FROM files WHERE id=%s", (f["id"],))
        deleted += 1

    db.commit()
    cursor.close()
    db.close()

    return {"message": f"{deleted} duplicates deleted"}

@app.route("/clean-selected-duplicates", methods=["POST"])
def clean_selected_duplicates():
    data = request.json
    hashes = data.get("hashes", [])

    if not hashes:
        return {"message": "No duplicates selected"}

    db = get_db()
    cursor = db.cursor(dictionary=True)

    total_deleted = 0

    for file_hash in hashes:

        cursor.execute("""
            SELECT id, path, importance, views
            FROM files
            WHERE file_hash=%s
            ORDER BY importance DESC, views DESC
        """, (file_hash,))

        files = cursor.fetchall()

        if len(files) <= 1:
            continue

        keep_file = files[0]

        # 🔥 DELETE ALL EXCEPT BEST
        for f in files[1:]:
            try:
                if os.path.exists(f["path"]):
                    os.remove(f["path"])   # ✅ DELETE REAL FILE
            except Exception as e:
                print("File delete error:", e)

            cursor.execute("DELETE FROM files WHERE id=%s", (f["id"],))
            total_deleted += 1

    db.commit()
    cursor.close()
    db.close()

    return {
        "message": "Selected duplicates cleaned",
        "deleted_files": total_deleted
    }
    
    
    
@app.route("/useless")
def useless_files():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
    SELECT * FROM files
    WHERE importance < 0.2 AND views = 0
    ORDER BY importance ASC
    """)

    data = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(data)

    
# ================= SEARCH =================
@app.route("/search")
def search():
    q = request.args.get("q", "")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM files
        WHERE name LIKE %s OR type LIKE %s
    """, (f"%{q}%", f"%{q}%"))

    data = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(data)

# ================= STATS =================
@app.route("/stats")
def stats():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM files")
    total = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return {"total_files": total}

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)