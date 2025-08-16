from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid

from ..models.models import BlinkSession, BlinkData
from ..schemas.blink import SessionCreate, SessionUpdate, BlinkBatch

class BlinkCRUD:
    """Blink data CRUD operations"""
    
    def create_session(self, db: Session, user_id: uuid.UUID, session: SessionCreate) -> BlinkSession:
        """Create new blink session"""
        db_session = BlinkSession(
            user_id=user_id,
            device_id=session.device_id,
            start_time=datetime.utcnow(),
            app_version=session.app_version,
            os_info=session.os_info
        )
        
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        return db_session
    
    def get_session(self, db: Session, session_id: uuid.UUID) -> Optional[BlinkSession]:
        """Get session by ID"""
        return db.query(BlinkSession).filter(BlinkSession.id == session_id).first()
    
    def update_session(self, db: Session, session_id: uuid.UUID, session_update: SessionUpdate) -> Optional[BlinkSession]:
        """Update session"""
        session = self.get_session(db, session_id)
        if not session:
            return None
        
        update_data = session_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(session, field, value)
        
        # Calculate duration if end_time is set
        if session.end_time and session.start_time:
            duration = session.end_time - session.start_time
            session.session_duration_seconds = int(duration.total_seconds())
        
        db.commit()
        db.refresh(session)
        
        return session
    
    def end_session(self, db: Session, session_id: uuid.UUID) -> Optional[BlinkSession]:
        """End session"""
        session = self.get_session(db, session_id)
        if not session:
            return None
        
        session.end_time = datetime.utcnow()
        
        # Calculate total blinks and duration
        total_blinks = db.query(func.sum(BlinkData.blink_count)).filter(
            BlinkData.session_id == session_id
        ).scalar() or 0
        
        session.total_blinks = total_blinks
        
        if session.start_time:
            duration = session.end_time - session.start_time
            session.session_duration_seconds = int(duration.total_seconds())
        
        db.commit()
        db.refresh(session)
        
        return session
    
    def store_blink_batch(self, db: Session, blink_batch: BlinkBatch) -> int:
        """Store batch of blink data"""
        session = self.get_session(db, blink_batch.session_id)
        if not session:
            return 0
        
        blink_records = []
        for data_point in blink_batch.blink_data:
            blink_record = BlinkData(
                session_id=blink_batch.session_id,
                timestamp=data_point.timestamp,
                blink_count=data_point.blink_count,
                confidence_score=data_point.confidence_score,
                eye_strain_score=data_point.eye_strain_score,
                interval_seconds=data_point.interval_seconds
            )
            blink_records.append(blink_record)
        
        db.add_all(blink_records)
        db.commit()
        
        return len(blink_records)
    
    def get_user_sessions(self, db: Session, user_id: uuid.UUID, limit: int = 50, offset: int = 0) -> List[BlinkSession]:
        """Get user sessions with pagination"""
        return db.query(BlinkSession).filter(
            BlinkSession.user_id == user_id
        ).order_by(desc(BlinkSession.start_time)).offset(offset).limit(limit).all()
    
    def get_session_data(self, db: Session, session_id: uuid.UUID, limit: int = 1000, offset: int = 0) -> List[BlinkData]:
        """Get blink data for session"""
        return db.query(BlinkData).filter(
            BlinkData.session_id == session_id
        ).order_by(BlinkData.timestamp).offset(offset).limit(limit).all()
    
    def get_user_analytics(self, db: Session, user_id: uuid.UUID, days: int = 30) -> Dict[str, Any]:
        """Get analytics for user"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Get sessions in period
        sessions = db.query(BlinkSession).filter(
            and_(
                BlinkSession.user_id == user_id,
                BlinkSession.start_time >= since_date
            )
        ).all()
        
        if not sessions:
            return {
                "total_sessions": 0,
                "total_blinks": 0,
                "average_blinks_per_minute": 0.0,
                "average_session_duration": 0.0,
                "eye_strain_average": None
            }
        
        # Calculate metrics
        total_sessions = len(sessions)
        total_blinks = sum(s.total_blinks for s in sessions if s.total_blinks)
        total_duration = sum(s.session_duration_seconds for s in sessions if s.session_duration_seconds)
        
        # Get blink data for strain calculation
        session_ids = [s.id for s in sessions]
        blink_data = db.query(BlinkData).filter(
            BlinkData.session_id.in_(session_ids)
        ).all()
        
        avg_eye_strain = None
        if blink_data:
            strain_scores = [bd.eye_strain_score for bd in blink_data if bd.eye_strain_score is not None]
            if strain_scores:
                avg_eye_strain = sum(strain_scores) / len(strain_scores)
        
        return {
            "total_sessions": total_sessions,
            "total_blinks": total_blinks,
            "average_blinks_per_minute": (total_blinks / (total_duration / 60)) if total_duration else 0.0,
            "average_session_duration": total_duration / total_sessions if total_sessions else 0.0,
            "eye_strain_average": avg_eye_strain
        }
    
    def export_user_data(self, db: Session, user_id: uuid.UUID) -> Dict[str, Any]:
        """Export all user data for GDPR compliance"""
        sessions = db.query(BlinkSession).filter(BlinkSession.user_id == user_id).all()
        
        session_ids = [s.id for s in sessions]
        blink_data = []
        if session_ids:
            blink_data = db.query(BlinkData).filter(BlinkData.session_id.in_(session_ids)).all()
        
        return {
            "user_id": str(user_id),
            "export_timestamp": datetime.utcnow().isoformat(),
            "sessions": [
                {
                    "id": str(s.id),
                    "device_id": s.device_id,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat() if s.end_time else None,
                    "total_blinks": s.total_blinks,
                    "duration_seconds": s.session_duration_seconds,
                    "app_version": s.app_version,
                    "os_info": s.os_info
                }
                for s in sessions
            ],
            "blink_data": [
                {
                    "id": str(bd.id),
                    "session_id": str(bd.session_id),
                    "timestamp": bd.timestamp.isoformat(),
                    "blink_count": bd.blink_count,
                    "confidence_score": bd.confidence_score,
                    "eye_strain_score": bd.eye_strain_score,
                    "interval_seconds": bd.interval_seconds
                }
                for bd in blink_data
            ]
        }
    
    def delete_user_data(self, db: Session, user_id: uuid.UUID) -> bool:
        """Delete all user data for GDPR compliance"""
        try:
            # Delete blink data first (due to foreign keys)
            sessions = db.query(BlinkSession).filter(BlinkSession.user_id == user_id).all()
            session_ids = [s.id for s in sessions]
            
            if session_ids:
                db.query(BlinkData).filter(BlinkData.session_id.in_(session_ids)).delete(synchronize_session=False)
            
            # Delete sessions
            db.query(BlinkSession).filter(BlinkSession.user_id == user_id).delete(synchronize_session=False)
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return False

blink_crud = BlinkCRUD()