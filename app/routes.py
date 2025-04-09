from flask import render_template, jsonify, request
from app import app, socketio
from app.camera import VideoProcessor
from flask_socketio import emit

# 建立全域視訊處理物件
video_processor = VideoProcessor()

@app.route('/')
def index():
    """渲染首頁"""
    return render_template('index.html')

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
        emit('processed_frame', result)

@app.route('/start_processing', methods=['POST'])
def start_processing():
    """啟動影像處理"""
    video_processor.enable_processing()
    return jsonify({"status": "success", "message": "處理已啟動"})

@app.route('/stop_processing', methods=['POST'])
def stop_processing():
    """停止影像處理"""
    video_processor.disable_processing()
    return jsonify({"status": "success", "message": "處理已停止"})