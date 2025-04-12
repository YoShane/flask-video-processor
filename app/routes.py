from flask import render_template, jsonify, request, redirect, url_for
from app import app, socketio, db
from app.camera import VideoProcessor
from app.models import ProcessingRecord
from flask_socketio import emit
from datetime import datetime

# 建立全域視訊處理物件
video_processor = VideoProcessor()
processing_start_time = None
count_values = []

@app.route('/')
def index():
    """渲染首頁"""
    records = ProcessingRecord.query.order_by(ProcessingRecord.timestamp.desc()).all()
    return render_template('index.html', records=records)

@socketio.on('connect')
def handle_connect():
    """處理新的 WebSocket 連接"""
    print("使用者端已連接")
    emit('status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """處理 WebSocket 斷開連接"""
    print("使用者端已斷開連接")

@socketio.on('frame')
def handle_frame(data):
    """
    接收並處理前端傳來的視訊畫面
    data: 包含 base64 編碼的圖片數據
    """
    if 'image' in data:
        result = video_processor.process_frame(data['image'])
        # 如果是略過的影格，不發送任何回應
        if 'skip' in result and result['skip']:
            return
        
        # 如果處理中且有計數資料，則收集計數
        if video_processor.processing_enabled and 'count' in result:
            count_values.append(result['count'])
            
        emit('processed_frame', result)

@app.route('/start_processing', methods=['POST'])
def start_processing():
    """啟動影像處理"""
    global processing_start_time, count_values
    processing_start_time = datetime.now()
    count_values = []
    video_processor.enable_processing()
    return jsonify({"status": "success", "message": "處理已啟動"})

@app.route('/stop_processing', methods=['POST'])
def stop_processing():
    """停止影像處理"""
    global processing_start_time, count_values
    video_processor.disable_processing()
    
    # 計算平均計數
    avg_count = 0
    if count_values:
        avg_count = sum(count_values) / len(count_values)
    
    # 取得最後一幀處理過的影像
    latest_image = ""
    if video_processor.latest_processed is not None:
        import cv2
        import base64
        _, jpeg = cv2.imencode('.jpg', video_processor.latest_processed)
        latest_image = base64.b64encode(jpeg.tobytes()).decode('utf-8')
    
    # 建立記錄
    if processing_start_time:
        new_record = ProcessingRecord(
            timestamp=processing_start_time,
            image=latest_image,
            name=f"記錄 {ProcessingRecord.query.count() + 1}",
            avg_count=round(avg_count, 2)
        )
        db.session.add(new_record)
        db.session.commit()
        
    return jsonify({
        "status": "success", 
        "message": "處理已停止",
        "record_id": new_record.id if 'new_record' in locals() else None
    })

@app.route('/records')
def get_records():
    """取得所有記錄"""
    records = ProcessingRecord.query.order_by(ProcessingRecord.timestamp.desc()).all()
    return jsonify([record.to_dict() for record in records])

@app.route('/record/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    """刪除記錄"""
    record = ProcessingRecord.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    return jsonify({"status": "success", "message": "記錄已刪除"})

@app.route('/record/<int:record_id>', methods=['PUT'])
def update_record(record_id):
    """更新記錄名稱"""
    record = ProcessingRecord.query.get_or_404(record_id)
    data = request.json
    if 'name' in data:
        record.name = data['name']
        db.session.commit()
        return jsonify({"status": "success", "message": "記錄已更新"})
    return jsonify({"status": "error", "message": "未提供名稱"}), 400