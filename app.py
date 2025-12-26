from flask import Flask, request, render_template, session, redirect, url_for
import os
import sqlite3
import os
os.environ["YOLO_CONFIG_DIR"] = "/your/custom/path"
from ultralytics import YOLO
from datetime import datetime

app = Flask(__name__)
app.secret_key = "xun-secret-key"
UPLOAD_FOLDER = "static/uploads"
DB_PATH = "lost_found.db"
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 限制圖片大小為 2MB
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 初始化資料庫
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        location TEXT,
        time TEXT,
        description TEXT,
        image_path TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# 查詢資料庫
def search_db(keyword):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE name LIKE ?", (f"%{keyword}%",))
    rows = cursor.fetchall()
    conn.close()
    return rows

# 取得最新拾獲物品
def get_latest_items(limit=5):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{
        "img": row[5],
        "name": row[1],
        "location": row[2],
        "time": row[3],
        "description": row[4]
    } for row in rows]

# 載入 YOLO 模型
model = YOLO("yolov8n.pt")

def detect_item(img_path):
    results = model.predict(img_path, device="cpu", verbose=False)
    detected_items = []
    for r in results:
        for c in r.boxes.cls:
            cls_name = model.names[int(c)]
            detected_items.append(cls_name)
    return detected_items

@app.route('/')
def home():
    return render_template('home.html')

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return render_template("search.html")  # 顯示搜尋表單頁面

    # POST：處理圖片與描述搜尋
    old_file = session.pop("last_uploaded", None)
    if old_file:
        old_path = os.path.join(UPLOAD_FOLDER, old_file)
        if os.path.exists(old_path) and old_path.startswith(UPLOAD_FOLDER):
            os.remove(old_path)

    photo = request.files.get("photo")
    description = request.form.get("description", "").strip()
    save_path = None
    filename = None

    if photo and photo.filename:
        filename = datetime.now().strftime("%Y%m%d%H%M%S_") + photo.filename
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        photo.save(save_path)
        session["last_uploaded"] = filename

    detected = detect_item(save_path) if save_path else []
    tags = list(set(detected + ([description] if description else [])))

    tagged_results = {}
    for tag in tags:
        tagged_results[tag] = []
        for row in search_db(tag):
            item = {
                "img": row[5],
                "name": row[1],
                "location": row[2],
                "time": row[3],
                "description": row[4]
            }
            if item not in tagged_results[tag]:
                tagged_results[tag].append(item)

    latest_items = get_latest_items()
    return render_template("search.html", tagged_results=tagged_results, tags=tags, latest_items=latest_items)

@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        photo = request.files.get("photo")
        name = request.form.get("name")
        location = request.form.get("location")
        time = request.form.get("time")
        description = request.form.get("description")

        filename = None
        if photo and photo.filename:
            filename = datetime.now().strftime("%Y%m%d%H%M%S_") + photo.filename
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            photo.save(save_path)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO items (name, location, time, description, image_path) VALUES (?, ?, ?, ?, ?)",
                  (name, location, time, description, f"uploads/{filename}" if filename else None))
        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    return render_template("report.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)