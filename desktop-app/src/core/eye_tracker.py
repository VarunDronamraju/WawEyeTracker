import cv2
import numpy as np
import threading
import time
from queue import Queue, Empty
from PyQt6.QtCore import QObject, pyqtSignal
from scipy.spatial import distance as dist

class EyeTracker(QObject):
    # Signals
    blink_detected = pyqtSignal()
    frame_processed = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # OpenCV components
        self.camera = None
        self.face_cascade = None
        self.eye_cascade = None
        
        # Tracking state
        self.is_tracking = False
        self.blink_count = 0
        self.last_blink_time = 0
        
        # Threading
        self.capture_thread = None
        self.process_thread = None
        self.frame_queue = Queue(maxsize=10)
        
        # Eye Aspect Ratio (EAR) for blink detection
        self.EAR_THRESHOLD = 0.25
        self.EAR_CONSEC_FRAMES = 3
        self.ear_counter = 0
        
        # Initialize OpenCV cascades
        self.init_cascades()
        
    def init_cascades(self):
        """Initialize OpenCV Haar cascades"""
        try:
            # Load pre-trained cascades
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            self.eye_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_eye.xml'
            )
        except Exception as e:
            self.error_occurred.emit(f"Failed to load cascades: {str(e)}")
            
    def start_tracking(self):
        """Start eye tracking"""
        if self.is_tracking:
            return
            
        try:
            # Initialize camera
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                raise Exception("Could not open camera")
                
            # Set camera properties for optimal performance
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            self.is_tracking = True
            self.blink_count = 0
            
            # Start threads
            self.capture_thread = threading.Thread(target=self._capture_frames)
            self.process_thread = threading.Thread(target=self._process_frames)
            
            self.capture_thread.start()
            self.process_thread.start()
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to start tracking: {str(e)}")
            
    def stop_tracking(self):
        """Stop eye tracking"""
        self.is_tracking = False
        
        # Wait for threads to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)
            
        if self.process_thread and self.process_thread.is_alive():
            self.process_thread.join(timeout=1.0)
            
        # Release camera
        if self.camera:
            self.camera.release()
            self.camera = None
            
        # Clear frame queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except Empty:
                break
                
    def _capture_frames(self):
        """Capture frames from camera (runs in separate thread)"""
        while self.is_tracking and self.camera:
            ret, frame = self.camera.read()
            if ret:
                # Add frame to queue if there's space
                if not self.frame_queue.full():
                    self.frame_queue.put(frame)
            else:
                time.sleep(0.01)  # Small delay if no frame
                
    def _process_frames(self):
        """Process frames for blink detection (runs in separate thread)"""
        while self.is_tracking:
            try:
                # Get frame from queue
                frame = self.frame_queue.get(timeout=0.1)
                
                # Process frame for blink detection
                self._detect_blinks(frame)
                
                # Emit processed frame
                self.frame_processed.emit(frame)
                
            except Empty:
                continue
            except Exception as e:
                self.error_occurred.emit(f"Frame processing error: {str(e)}")
                
    def _detect_blinks(self, frame):
        """Detect blinks in frame using Eye Aspect Ratio"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
            
            for (x, y, w, h) in faces:
                # Extract face region
                face_gray = gray[y:y+h, x:x+w]
                
                # Detect eyes in face region
                eyes = self.eye_cascade.detectMultiScale(face_gray)
                
                if len(eyes) >= 2:
                    # Calculate Eye Aspect Ratio for detected eyes
                    ear = self._calculate_eye_aspect_ratio(eyes, face_gray)
                    
                    # Check for blink
                    if ear < self.EAR_THRESHOLD:
                        self.ear_counter += 1
                    else:
                        # If eyes were closed for sufficient frames, register blink
                        if self.ear_counter >= self.EAR_CONSEC_FRAMES:
                            current_time = time.time()
                            
                            # Avoid double counting (minimum 200ms between blinks)
                            if current_time - self.last_blink_time > 0.2:
                                self.blink_count += 1
                                self.last_blink_time = current_time
                                self.blink_detected.emit()
                                
                        self.ear_counter = 0
                        
        except Exception as e:
            self.error_occurred.emit(f"Blink detection error: {str(e)}")
            
    def _calculate_eye_aspect_ratio(self, eyes, face_gray):
        """Calculate Eye Aspect Ratio (simplified version)"""
        try:
            # This is a simplified EAR calculation
            # In a full implementation, you'd use landmark detection
            if len(eyes) < 2:
                return 1.0
                
            # Sort eyes by x coordinate
            eyes = sorted(eyes, key=lambda e: e[0])
            
            # Calculate basic ratio based on eye height/width
            total_ratio = 0
            for (ex, ey, ew, eh) in eyes[:2]:  # Use first two eyes
                ratio = eh / ew if ew > 0 else 1.0
                total_ratio += ratio
                
            return total_ratio / 2
            
        except Exception:
            return 1.0  # Default to "eyes open"
            
    def get_blink_count(self):
        """Get current blink count"""
        return self.blink_count
        
    def reset_blink_count(self):
        """Reset blink count"""
        self.blink_count = 0
        
    def is_camera_available(self):
        """Check if camera is available"""
        try:
            cap = cv2.VideoCapture(0)
            available = cap.isOpened()
            cap.release()
            return available
        except Exception:
            return False