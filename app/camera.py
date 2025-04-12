import cv2
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import re

class VideoProcessor:
    """
    處理從前端發送的串流畫面
    """
    def __init__(self):
        # 設置 matplotlib 為非互動模式
        plt.ioff()
        plt.switch_backend('Agg')  # 使用非互動式後端
        self.processing_enabled = False
        self.current_threshold = 0
        self.grey_frame = None
        self.latest_frame = None
        self.latest_processed = None
        self.latest_histogram = None
        self.is_processing = False  # 增加一個標記，表示目前是否正在處理影格
        self.skip_count = 0  # 記錄略過的影格數量
    
    def enable_processing(self):
        self.processing_enabled = True
    
    def disable_processing(self):
        self.processing_enabled = False
    
    def process_frame(self, frame_data):
        """
        處理從前端傳來的視訊畫面，增加略過機制避免負載過高
        """
        # 如果當前正在處理影格，則略過這一幀
        if self.is_processing:
            self.skip_count += 1
            if self.skip_count % 30 == 0: #每略過 30 幀時在控制台輸出一條訊息
                print(f"略過影格，已略過 {self.skip_count} 幀")
            return {"skip": True}
        
        self.is_processing = True  # 標記為處理中
        
        try:
            # 移除 data:image/jpeg;base64, 前綴
            if 'base64,' in frame_data:
                frame_data = frame_data.split('base64,')[1]
            
            # 解碼 base64 
            img_data = base64.b64decode(frame_data)
            np_arr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            width = frame.shape[1]
            height = frame.shape[0]
            frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
            
            self.latest_frame = frame
            self.grey_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 處理畫面
            result = self._process_image(frame)
            return result
        except Exception as e:
            print(f"處理畫面時發生錯誤: {e}")
            return {"error": str(e)}
        finally:
            self.is_processing = False  # 標記為處理完成
    
    def _process_image(self, frame):
        """
        內部方法：處理圖像並回傳處理結果
        """
        output = frame.copy()
        
        if self.processing_enabled:
            # 二值化處理（自動閾值）
            self.current_threshold, binary_img = cv2.threshold(self.grey_frame, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # 輪廓偵測
            contours, hierarchy = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            n = len(contours)  # ✅ 計算輪廓數量

            # 用矩形畫輪廓
            for i in range(n):
                x, y, w, h = cv2.boundingRect(contours[i])
                brcnt = np.array([[[x, y]], [[x + w, y]], [[x + w, y + h]], [[x, y + h]]])
                cv2.drawContours(output, [brcnt], -1, (0, 0, 255), 2)

            # ✅ 顯示數量在畫面上
            cv2.putText(output, f'Count: {n}', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)

            # 降低直方圖更新頻率 - 每5幀更新一次
            if not hasattr(self, 'histogram_update_counter'):
                self.histogram_update_counter = 0
            
            self.histogram_update_counter += 1
            if self.histogram_update_counter >= 5:
                self._update_histogram()
                self.histogram_update_counter = 0
        else:
            histogram_b64 = ""
            n = 0  # 未處理時數量為0
        
        # 儲存最新處理過的畫面
        self.latest_processed = output
        
        # 將處理後的畫面轉為 base64 - 提高壓縮率
        ret, jpeg = cv2.imencode('.jpg', output, [cv2.IMWRITE_JPEG_QUALITY, 80])
        processed_b64 = base64.b64encode(jpeg.tobytes()).decode('utf-8')
        
        result = {
            "processed_image": processed_b64,
            "processing_enabled": self.processing_enabled,
            "count": n  # 加入計數到結果中
        }
        
        # 只有當處理啟用時才傳送直方圖和閾值
        if self.processing_enabled and self.latest_histogram is not None:
            histogram_b64 = base64.b64encode(self.latest_histogram).decode('utf-8')
            result.update({
                "histogram": histogram_b64,
                "threshold": int(self.current_threshold)
            })
        
        return result

    def _update_histogram(self):
        """
        更新直方圖圖像 - 極度簡化版本以提高效率
        """
        if self.grey_frame is None:
            return
        
        # 大幅縮小樣本以加速處理
        # 只用灰階圖的1/4樣本來生成直方圖
        sampled_gray = self.grey_frame[::2, ::2]
        
        # 建立更小的圖形
        plt.figure(figsize=(4, 2), dpi=70)
        plt.clf()
        plt.hist(sampled_gray.ravel(), 64, [0, 256], color='gray')
        plt.axvline(self.current_threshold, color='red', linestyle='dashed', linewidth=2, label=f'T: {int(self.current_threshold)}')
        plt.title('Real-time Grayscale Histogram with Otsu Threshold')
        plt.xlabel('Pixel Value')
        plt.ylabel('Frequency')
        plt.tight_layout(pad=0.5)
        
        # 將圖表轉為低品質圖像
        buf = BytesIO()
        plt.savefig(buf, format='jpeg', dpi=70, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        # 儲存直方圖圖像
        self.latest_histogram = buf.getvalue()