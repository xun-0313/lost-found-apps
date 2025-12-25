from flask import Flask, request, render_template
import os
import sqlite3
from ultralytics import YOLO
from datetime import datetime

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
def detect_item(img_path):
    model = YOLO("yolov8n.pt")  # 每次呼叫時才載入
    results = model.predict(img_path, verbose=False)
init_db()

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

@app.route("/search", methods=["POST"])
def search():
    photo = request.files.get("photo")
    description = request.form.get("description", "").strip()
    save_path = None

    # 儲存圖片
    if photo and photo.filename:
        filename = datetime.now().strftime("%Y%m%d%H%M%S_") + photo.filename
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        photo.save(save_path)

    # YOLO 辨識
    detected = detect_item(save_path) if save_path else []

    # 結合描述與辨識關鍵字
    keywords = detected + ([description] if description else [])

    # 查詢資料庫
    results = []
    for kw in keywords:
        for row in search_db(kw):
            item = {
                "img": row[4],
                "name": row[1],
                "location": row[2],
                "time": row[3]
            }
            if item not in results:
                results.append(item)

    return render_template("index.html", results=results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)