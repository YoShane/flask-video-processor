from datetime import datetime
import pytz
from app import db

class ProcessingRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    image = db.Column(db.Text)  # Store base64 encoded image
    name = db.Column(db.String(100), default="未命名")
    avg_count = db.Column(db.Float)
    
    def to_dict(self):
        # 設定台灣時區
        taiwan_tz = pytz.timezone('Asia/Taipei')
        
        # 將 UTC 時間轉換為台灣時間
        local_time = pytz.utc.localize(self.timestamp).astimezone(taiwan_tz)
        
        return {
            'id': self.id,
            'timestamp': local_time.strftime('%Y-%m-%d %H:%M:%S'),
            'image': self.image,
            'name': self.name,
            'avg_count': self.avg_count
        }