import cv2
import threading
import queue
import time
import numpy as np
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from collections import deque

@dataclass
class BlinkEvent:
    timestamp: float
    confidence: float
    eye_aspect_ratio: float
    frame_number: int

@dataclass
class TrackingStats:
    frames_processed: int = 0
    blinks_detected: int = 0
    average_fps: float = 0.0
    average_latency: float = 0.0
    cpu_usage: float = 0.0

class EyeTrackingEngine:
    def __init__(self):
        self.camera = None
        self.is_running = False
        self.is_paused = False
        
        # Threading components
        self.frame_queue = queue.Queue(maxsize=10)
        self.blink_queue = queue.Queue()
        self.capture_thread = None
        self.process_thread = None
        
        # OpenCV components
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        # Blink detection parameters
        self.EYE_AR_THRESH = 0.25  # Eye aspect ratio threshold
        self.EYE_AR_CONSEC_FRAMES = 3  # Consecutive frames for blink
        self.COUNTER = 0
        self.TOTAL_BLINKS = 0
        
        # Performance tracking
        self.stats = TrackingStats()
        self.frame_times = deque(maxlen=30)  # Last 30 frame times
        self.process_times = deque(maxlen=30)  # Last 30 processing times
        
        # Callbacks
        self.on_blink_detected: Optional[Callable[[BlinkEvent], None]] = None
        self.on_stats_updated: Optional[Callable[[TrackingStats], None]] = None
        
    def start_tracking(self) -> bool:
        """Start eye tracking with camera initialization"""
        try:
            # Initialize camera
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                raise Exception("Could not open camera")
            
            # Set camera properties for performance
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 20)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            self.is_running = True
            self.is_paused = False
            
            # Start threads
            self.capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
            self.process_thread = threading.Thread(target=self._process_frames, daemon=True)
            
            self.capture_thread.start()
            self.process_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Failed to start tracking: {e}")
            return False
    
    def stop_tracking(self):
        """Stop eye tracking and cleanup resources"""
        self.is_running = False
        
        # Wait for threads to finish
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
        if self.process_thread:
            self.process_thread.join(timeout=2.0)
        
        # Release camera
        if self.camera:
            self.camera.release()
            self.camera = None
        
        # Clear queues
        self._clear_queue(self.frame_queue)
        self._clear_queue(self.blink_queue)
    
    def pause_tracking(self):
        """Pause tracking without stopping camera"""
        self.is_paused = True
    
    def resume_tracking(self):
        """Resume tracking"""
        self.is_paused = False
    
    def _capture_frames(self):
        """Capture frames from camera in separate thread"""
        frame_count = 0
        
        while self.is_running:
            if self.is_paused:
                time.sleep(0.1)
                continue
                
            start_time = time.time()
            
            ret, frame = self.camera.read()
            if not ret:
                print("Failed to capture frame")
                continue
            
            frame_count += 1
            
            # Add frame to queue (non-blocking)
            try:
                self.frame_queue.put((frame, frame_count, start_time), block=False)
            except queue.Full:
                # Skip frame if queue is full (prevents memory buildup)
                pass
            
            # Track frame capture timing
            self.frame_times.append(time.time() - start_time)
            
            # Limit to 20 FPS
            time.sleep(0.05)
    
    def _process_frames(self):
        """Process frames for blink detection in separate thread"""
        while self.is_running:
            try:
                # Get frame from queue (blocking with timeout)
                frame, frame_number, capture_time = self.frame_queue.get(timeout=0.1)
                
                if self.is_paused:
                    continue
                
                process_start = time.time()
                
                # Detect blink
                blink_event = self._detect_blink(frame, frame_number, capture_time)
                
                if blink_event:
                    # Add to blink queue
                    self.blink_queue.put(blink_event)
                    
                    # Call callback if set
                    if self.on_blink_detected:
                        self.on_blink_detected(blink_event)
                
                # Update performance stats
                process_time = time.time() - process_start
                self.process_times.append(process_time)
                self._update_stats(frame_number, process_time)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing frame: {e}")
                continue
    
    def _detect_blink(self, frame: np.ndarray, frame_number: int, capture_time: float) -> Optional[BlinkEvent]:
        """Detect blink in frame using eye aspect ratio"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            for (x, y, w, h) in faces:
                # Region of interest (face)
                roi_gray = gray[y:y+h, x:x+w]
                
                # Detect eyes in face
                eyes = self.eye_cascade.detectMultiScale(roi_gray, 1.1, 3)
                
                if len(eyes) >= 2:
                    # Calculate eye aspect ratio
                    eye_ar = self._calculate_eye_aspect_ratio(eyes, roi_gray)
                    
                    # Check if blink detected
                    if eye_ar < self.EYE_AR_THRESH:
                        self.COUNTER += 1
                    else:
                        # Check if blink occurred
                        if self.COUNTER >= self.EYE_AR_CONSEC_FRAMES:
                            self.TOTAL_BLINKS += 1
                            
                            # Create blink event
                            confidence = self._calculate_blink_confidence(eye_ar)
                            
                            return BlinkEvent(
                                timestamp=capture_time,
                                confidence=confidence,
                                eye_aspect_ratio=eye_ar,
                                frame_number=frame_number
                            )
                        
                        self.COUNTER = 0
            
            return None
            
        except Exception as e:
            print(f"Error in blink detection: {e}")
            return None
    
    def _calculate_eye_aspect_ratio(self, eyes: np.ndarray, roi_gray: np.ndarray) -> float:
        """Calculate eye aspect ratio for blink detection"""
        if len(eyes) < 2:
            return 0.3  # Default value
        
        # Use the two largest eye regions
        eyes_sorted = sorted(eyes, key=lambda e: e[2] * e[3], reverse=True)
        eye1, eye2 = eyes_sorted[0], eyes_sorted[1]
        
        # Simple aspect ratio calculation
        # In a real implementation, you might use dlib landmarks
        eye1_ar = eye1[3] / eye1[2] if eye1[2] > 0 else 0.3
        eye2_ar = eye2[3] / eye2[2] if eye2[2] > 0 else 0.3
        
        return (eye1_ar + eye2_ar) / 2.0
    
    def _calculate_blink_confidence(self, eye_ar: float) -> float:
        """Calculate confidence score for blink detection"""
        # Confidence based on how far below threshold
        if eye_ar < self.EYE_AR_THRESH:
            confidence = (self.EYE_AR_THRESH - eye_ar) / self.EYE_AR_THRESH
            return min(confidence, 1.0)
        return 0.0
    
    def _update_stats(self, frame_number: int, process_time: float):
        """Update tracking statistics"""
        self.stats.frames_processed = frame_number
        self.stats.blinks_detected = self.TOTAL_BLINKS
        
        # Calculate average FPS
        if len(self.frame_times) > 0:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            self.stats.average_fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        
        # Calculate average latency
        if len(self.process_times) > 0:
            self.stats.average_latency = sum(self.process_times) / len(self.process_times) * 1000  # ms
        
        # Call stats callback every 30 frames
        if frame_number % 30 == 0 and self.on_stats_updated:
            self.on_stats_updated(self.stats)
    
    def _clear_queue(self, q: queue.Queue):
        """Clear queue without blocking"""
        try:
            while True:
                q.get_nowait()
        except queue.Empty:
            pass
    
    def get_latest_blinks(self) -> list[BlinkEvent]:
        """Get all blinks from queue"""
        blinks = []
        try:
            while True:
                blinks.append(self.blink_queue.get_nowait())
        except queue.Empty:
            pass
        return blinks
    
    def get_stats(self) -> TrackingStats:
        """Get current tracking statistics"""
        return self.stats
    
    def set_blink_callback(self, callback: Callable[[BlinkEvent], None]):
        """Set callback for blink events"""
        self.on_blink_detected = callback
    
    def set_stats_callback(self, callback: Callable[[TrackingStats], None]):
        """Set callback for stats updates"""
        self.on_stats_updated = callback