import cv2
import numpy as np
from typing import Tuple, List, Optional
import dlib
from scipy.spatial import distance as dist

class AdvancedBlinkDetector:
    """Advanced blink detector using facial landmarks"""
    
    def __init__(self):
        # Initialize dlib's face detector and landmark predictor
        self.detector = dlib.get_frontal_face_detector()
        
        # Download shape_predictor_68_face_landmarks.dat if not available
        try:
            self.predictor = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")
            self.use_landmarks = True
        except:
            print("Landmark predictor not found, using basic detection")
            self.use_landmarks = False
        
        # Eye landmark indices
        self.LEFT_EYE_POINTS = list(range(36, 42))
        self.RIGHT_EYE_POINTS = list(range(42, 48))
        
        # Blink detection parameters
        self.EAR_THRESHOLD = 0.25
        self.CONSEC_FRAMES = 3
        
        # State tracking
        self.blink_counter = 0
        self.total_blinks = 0
    
    def eye_aspect_ratio(self, eye_points: np.ndarray) -> float:
        """Calculate eye aspect ratio from landmark points"""
        # Vertical eye landmarks
        A = dist.euclidean(eye_points[1], eye_points[5])
        B = dist.euclidean(eye_points[2], eye_points[4])
        
        # Horizontal eye landmark
        C = dist.euclidean(eye_points[0], eye_points[3])
        
        # Eye aspect ratio
        ear = (A + B) / (2.0 * C)
        return ear
    
    def detect_blink_landmarks(self, frame: np.ndarray) -> Tuple[bool, float, List[Tuple[int, int]]]:
        """Detect blink using facial landmarks"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.detector(gray)
        
        if len(faces) == 0:
            return False, 0.0, []
        
        # Use the first detected face
        face = faces[0]
        landmarks = self.predictor(gray, face)
        
        # Convert landmarks to numpy array
        points = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in range(68)])
        
        # Extract eye points
        left_eye = points[self.LEFT_EYE_POINTS]
        right_eye = points[self.RIGHT_EYE_POINTS]
        
        # Calculate eye aspect ratios
        left_ear = self.eye_aspect_ratio(left_eye)
        right_ear = self.eye_aspect_ratio(right_eye)
        
        # Average the eye aspect ratios
        ear = (left_ear + right_ear) / 2.0
        
        # Check for blink
        blink_detected = False
        if ear < self.EAR_THRESHOLD:
            self.blink_counter += 1
        else:
            if self.blink_counter >= self.CONSEC_FRAMES:
                self.total_blinks += 1
                blink_detected = True
            self.blink_counter = 0
        
        # Return eye points for visualization
        eye_points = np.concatenate([left_eye, right_eye])
        
        return blink_detected, ear, eye_points.tolist()
    
    def detect_blink_basic(self, frame: np.ndarray) -> Tuple[bool, float]:
        """Basic blink detection using Haar cascades"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Load Haar cascades
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 3)
            
            if len(eyes) >= 2:
                # Simple eye aspect ratio calculation
                eye_height = np.mean([eye[3] for eye in eyes])
                eye_width = np.mean([eye[2] for eye in eyes])
                ear = eye_height / eye_width if eye_width > 0 else 0.3
                
                # Check for blink
                blink_detected = False
                if ear < self.EAR_THRESHOLD:
                    self.blink_counter += 1
                else:
                    if self.blink_counter >= self.CONSEC_FRAMES:
                        self.total_blinks += 1
                        blink_detected = True
                    self.blink_counter = 0
                
                return blink_detected, ear
        
        return False, 0.3
    
    def detect_blink(self, frame: np.ndarray) -> Tuple[bool, float, Optional[List[Tuple[int, int]]]]:
        """Main blink detection method"""
        if self.use_landmarks:
            blink, ear, eye_points = self.detect_blink_landmarks(frame)
            return blink, ear, eye_points
        else:
            blink, ear = self.detect_blink_basic(frame)
            return blink, ear, None
    
    def reset_counters(self):
        """Reset blink counters"""
        self.blink_counter = 0
        self.total_blinks = 0
    
    def get_total_blinks(self) -> int:
        """Get total blinks detected"""
        return self.total_blinks