from flask import Flask, request, render_template
import os
import sqlite3
from ultralytics import YOLO

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 初始化資料庫
def init_db():
    conn = sqlite3.connect("lost_found.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        location TEXT,
        time TEXT,
        image_path TEXT
    )''')
    conn.commit()
    conn.close()

# 載入 YOLO 模型
model = YOLO("yolov8n.pt")
init_db()  # 確保 Render 啟動時也會建立資料庫

# 查詢資料庫
def search_db(keyword):
    conn = sqlite3.connect("lost_found.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE name LIKE ?", (f"%{keyword}%",))
    rows = cursor.fetchall()
    conn.close()
    return rows

# YOLO 辨識
def detect_item(img_path):
    results = model(img_path)
    detected_items = []
    for r in results:
        for c in r.boxes.cls:
            cls_name = model.names[int(c)]
            detected_items.append(cls_name)
    return detected_items

@app.route('/')
def home():
    return render_template('index.html', results=None)

@app.route('/search', methods=['POST'])
def search():
    description = request.form.get('description')
    photo = request.files.get('photo')

    filename = None
    detected_items = []
    if photo:
        filename = photo.filename
        img_path = os.path.join(UPLOAD_FOLDER, filename)
        photo.save(img_path)
        detected_items = detect_item(img_path)

    if description:
        db_results = search_db(description)
    elif detected_items:
        db_results = []
        for item in detected_items:
            db_results.extend(search_db(item))
    else:
        db_results = []

    results = [{"name": r[1], "location": r[2], "time": r[3], "img": r[4]} for r in db_results]
    return render_template("index.html", results=results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
