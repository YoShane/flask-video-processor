from flask import render_template, jsonify, request, redirect, url_for, session
from app import app, socketio, db
from app.camera import VideoProcessor
from app.models import ProcessingRecord
from flask_socketio import emit, join_room
from datetime import datetime
import uuid
import time
from threading import Timer

# 使用字典存儲每個使用者的視訊處理器和處理數據
video_processors = {}
processing_data = {}

# 清理不活躍的處理器的定時器函數
def cleanup_inactive_processors():
    """清理不活躍的處理程序"""
    current_time = time.time()
    inactive_threshold = 300  # 5分鐘無活動視為不活躍
    
    for sid in list(video_processors.keys()):
        processor = video_processors[sid]
        if hasattr(processor, 'last_activity'):
            if current_time - processor.last_activity > inactive_threshold:
                print(f"清理不活動的客戶端: {sid}")
                del video_processors[sid]
                if sid in processing_data:
                    del processing_data[sid]
    
    # 排程下一次清理
    Timer(60.0, cleanup_inactive_processors).start()

# 啟動清理定時器
cleanup_timer = Timer(60.0, cleanup_inactive_processors)
cleanup_timer.daemon = True
cleanup_timer.start()

@app.route('/')
def index():
    """渲染首頁"""
    # 確保每個用戶有唯一的session ID
    if 'client_id' not in session:
        session['client_id'] = str(uuid.uuid4())
    
    records = ProcessingRecord.query.order_by(ProcessingRecord.timestamp.desc()).all()
    return render_template('index.html', records=records)

@socketio.on('connect')
def handle_connect():
    """處理新的 WebSocket 連接"""
    sid = request.sid
    print(f"使用者端已連接: {sid}")
    
    # 為這個客戶端建立新的視訊處理器
    video_processors[sid] = VideoProcessor()
    video_processors[sid].last_activity = time.time()
    
    processing_data[sid] = {
        'start_time': None,
        'count_values': []
    }
    
    # 將客戶端加入一個以sid命名的房間
    join_room(sid)
    emit('status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """處理 WebSocket 斷開連接"""
    sid = request.sid
    print(f"使用者端已斷開連接: {sid}")
    
    # 清理資源
    if sid in video_processors:
        del video_processors[sid]
    if sid in processing_data:
        del processing_data[sid]

@socketio.on('frame')
def handle_frame(data):
    """
    接收並處理前端傳來的視訊畫面
    data: 包含 base64 編碼的圖片數據
    """
    sid = request.sid
    
    # 如果處理器不存在則建立一個
    if sid not in video_processors:
        video_processors[sid] = VideoProcessor()
        video_processors[sid].last_activity = time.time()
        processing_data[sid] = {
            'start_time': None,
            'count_values': []
        }
    
    # 更新最後活動時間
    video_processors[sid].last_activity = time.time()
    
    if 'image' in data:
        result = video_processors[sid].process_frame(data['image'])
        # 如果是略過的影格，不發送任何回應
        if 'skip' in result and result['skip']:
            return
        
        # 如果處理中且有計數資料，則收集計數
        if video_processors[sid].processing_enabled and 'count' in result:
            processing_data[sid]['count_values'].append(result['count'])
            
        # 只向發送請求的客戶端發送處理結果
        emit('processed_frame', result, room=sid)

@app.route('/start_processing', methods=['POST'])
def start_processing():
    """啟動影像處理"""
    sid = request.json.get('sid') if request.json else None
    
    # 如果沒有提供 sid，則使用 session 中的 client_id
    if not sid:
        sid = session.get('client_id')
    
    # 確保 sid 存在於處理器字典中
    if sid not in video_processors:
        video_processors[sid] = VideoProcessor()
        video_processors[sid].last_activity = time.time()
        processing_data[sid] = {
            'start_time': None,
            'count_values': []
        }
    
    processing_data[sid]['start_time'] = datetime.now()
    processing_data[sid]['count_values'] = []
    video_processors[sid].enable_processing()
    
    return jsonify({
        "status": "success", 
        "message": "處理已啟動",
        "sid": sid
    })

@app.route('/stop_processing', methods=['POST'])
def stop_processing():
    """停止影像處理"""
    sid = request.json.get('sid') if request.json else None
    
    # 如果沒有提供 sid，則使用 session 中的 client_id
    if not sid:
        sid = session.get('client_id')
    
    if sid not in video_processors:
        return jsonify({
            "status": "error", 
            "message": "找不到處理器",
            "sid": sid
        })
    
    video_processors[sid].disable_processing()
    
    # 計算平均計數
    avg_count = 0
    if processing_data[sid]['count_values']:
        avg_count = sum(processing_data[sid]['count_values']) / len(processing_data[sid]['count_values'])
    
    # 取得最後一幀處理過的影像
    latest_image = ""
    if video_processors[sid].latest_processed is not None:
        import cv2
        import base64
        _, jpeg = cv2.imencode('.jpg', video_processors[sid].latest_processed)
        latest_image = base64.b64encode(jpeg.tobytes()).decode('utf-8')
    
    # 建立記錄
    new_record = None
    if processing_data[sid]['start_time']:
        new_record = ProcessingRecord(
            timestamp=processing_data[sid]['start_time'],
            image=latest_image,
            name=f"記錄 {ProcessingRecord.query.count() + 1}",
            avg_count=round(avg_count, 2)
        )
        db.session.add(new_record)
        db.session.commit()
        
    return jsonify({
        "status": "success", 
        "message": "處理已停止",
        "record_id": new_record.id if new_record else None,
        "sid": sid
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