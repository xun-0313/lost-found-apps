from flask import Flask, request, render_template
import os
import sqlite3
from ultralytics import YOLO   # 使用新版 Ultralytics YOLO

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 載入 YOLO 模型 (建議用輕量版 yolov8n.pt，速度快)
model = YOLO("yolov8n.pt")

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
    results = model(img_path)  # 推論
    detected_items = []
    for r in results:
        for c in r.boxes.cls:   # 取得類別編號
            cls_name = model.names[int(c)]  # 轉換成物品名稱
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

    # 查詢邏輯
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
    init_db()
    app.run(host='0.0.0.0', port=3000, debug=True)
