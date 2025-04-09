# Flask Video Processor

This project is a Flask application that implements video stream processing from a webcam. It provides real-time video capture and allows for image processing techniques such as Otsu's thresholding and contour detection.

## Project Structure

```
flask-video-processor
├── app
│   ├── __init__.py
│   ├── routes.py
│   ├── camera.py
│   ├── processors
│   │   ├── __init__.py
│   │   ├── otsu.py
│   │   └── contour.py
│   ├── static
│   │   ├── css
│   │   │   └── style.css
│   │   └── js
│   │       └── main.js
│   └── templates
│       ├── base.html
│       ├── index.html
│       └── video.html
├── config.py
├── requirements.txt
├── run.py
└── README.md
```

## Features

- Real-time video streaming from the webcam.
- Image processing capabilities including Otsu's thresholding and contour detection.
- Responsive web interface for displaying video and processing options.

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd flask-video-processor
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python run.py
   ```

4. Open your web browser and navigate to `http://127.0.0.1:5000` to access the application.

## Usage

- The main page displays the video stream from the webcam.
- Users can navigate to the video processing page to apply different image processing techniques.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.