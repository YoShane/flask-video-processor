from datetime import datetime
from app import db

class ProcessingRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    image = db.Column(db.Text)  # Store base64 encoded image
    name = db.Column(db.String(100), default="未命名")
    avg_count = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'image': self.image,
            'name': self.name,
            'avg_count': self.avg_count
        }