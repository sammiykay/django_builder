"""
Redis-based Session Memory for Django AI Builder
Provides persistent conversation memory like Bolt.new
"""

import redis
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
import hashlib

logger = logging.getLogger(__name__)


class SessionMemoryManager:
    """
    Advanced session memory management using Redis
    Stores conversation history, context, and user preferences
    """
    
    def __init__(self, redis_client=None):
        if redis_client:
            self.redis = redis_client
        else:
            # Try to connect to Redis
            try:
                redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
                self.redis = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis.ping()
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                self.redis = None
        
        self.default_ttl = 86400 * 7  # 7 days
        self.max_history_items = 100
        self.context_cache = {}
    
    def create_session(self, user_id: str, project_id: str, session_type: str = 'conversation') -> str:
        """
        Create a new session and return session ID
        
        Args:
            user_id: User identifier
            project_id: Project identifier
            session_type: Type of session (conversation, generation, etc.)
            
        Returns:
            Session ID string
        """
        try:
            # Generate session ID
            session_data = f"{user_id}:{project_id}:{session_type}:{datetime.now().isoformat()}"
            session_id = hashlib.md5(session_data.encode()).hexdigest()
            
            # Initialize session
            initial_data = {
                'session_id': session_id,
                'user_id': user_id,
                'project_id': project_id,
                'session_type': session_type,
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'conversation_history': [],
                'context': {},
                'preferences': {},
                'state': 'active'
            }
            
            # Store in Redis
            if self.redis:
                self.redis.hset(
                    f"session:{session_id}",
                    mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in initial_data.items()}
                )
                self.redis.expire(f"session:{session_id}", self.default_ttl)
            else:
                # Fallback to Django cache
                cache.set(f"session:{session_id}", initial_data, self.default_ttl)
            
            logger.info(f"Created session {session_id} for user {user_id}, project {project_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve session data
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data dictionary or None
        """
        try:
            if self.redis:
                data = self.redis.hgetall(f"session:{session_id}")
                if data:
                    # Parse JSON fields
                    for key in ['conversation_history', 'context', 'preferences']:
                        if key in data:
                            try:
                                data[key] = json.loads(data[key])
                            except (json.JSONDecodeError, TypeError):
                                data[key] = [] if key == 'conversation_history' else {}
                    return data
            else:
                # Fallback to Django cache
                return cache.get(f"session:{session_id}")
                
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None
    
    def update_session_activity(self, session_id: str):
        """Update session last activity timestamp"""
        try:
            if self.redis:
                self.redis.hset(
                    f"session:{session_id}",
                    'last_activity',
                    datetime.now().isoformat()
                )
                self.redis.expire(f"session:{session_id}", self.default_ttl)
            else:
                session_data = cache.get(f"session:{session_id}")
                if session_data:
                    session_data['last_activity'] = datetime.now().isoformat()
                    cache.set(f"session:{session_id}", session_data, self.default_ttl)
                    
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")
    
    def add_message_to_history(self, session_id: str, message: Dict):
        """
        Add message to conversation history
        
        Args:
            session_id: Session identifier
            message: Message dictionary with role, content, timestamp, etc.
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                logger.warning(f"Session {session_id} not found")
                return False
            
            # Add timestamp if not present
            if 'timestamp' not in message:
                message['timestamp'] = datetime.now().isoformat()
            
            # Add to history
            history = session_data.get('conversation_history', [])
            history.append(message)
            
            # Keep only recent messages
            if len(history) > self.max_history_items:
                history = history[-self.max_history_items:]
            
            # Update session
            self.update_session_field(session_id, 'conversation_history', history)
            self.update_session_activity(session_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding message to history: {e}")
            return False
    
    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """
        Get conversation history for session
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return []
            
            history = session_data.get('conversation_history', [])
            return history[-limit:] if limit else history
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def update_session_context(self, session_id: str, context_updates: Dict):
        """
        Update session context with new information
        
        Args:
            session_id: Session identifier
            context_updates: Dictionary of context updates
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                logger.warning(f"Session {session_id} not found")
                return False
            
            # Merge context
            current_context = session_data.get('context', {})
            current_context.update(context_updates)
            
            # Update session
            self.update_session_field(session_id, 'context', current_context)
            self.update_session_activity(session_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating session context: {e}")
            return False
    
    def get_session_context(self, session_id: str) -> Dict:
        """
        Get session context
        
        Args:
            session_id: Session identifier
            
        Returns:
            Context dictionary
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return {}
            
            return session_data.get('context', {})
            
        except Exception as e:
            logger.error(f"Error getting session context: {e}")
            return {}
    
    def update_session_field(self, session_id: str, field: str, value: Any):
        """
        Update a specific field in session data
        
        Args:
            session_id: Session identifier
            field: Field name to update
            value: New value
        """
        try:
            if self.redis:
                # Serialize complex values
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                
                self.redis.hset(f"session:{session_id}", field, value)
                self.redis.expire(f"session:{session_id}", self.default_ttl)
            else:
                # Fallback to Django cache
                session_data = cache.get(f"session:{session_id}")
                if session_data:
                    session_data[field] = value
                    cache.set(f"session:{session_id}", session_data, self.default_ttl)
                    
        except Exception as e:
            logger.error(f"Error updating session field {field}: {e}")
    
    def get_user_sessions(self, user_id: str, project_id: str = None) -> List[Dict]:
        """
        Get all sessions for a user
        
        Args:
            user_id: User identifier
            project_id: Optional project filter
            
        Returns:
            List of session data dictionaries
        """
        try:
            sessions = []
            
            if self.redis:
                # Get all session keys
                pattern = f"session:*"
                keys = self.redis.keys(pattern)
                
                for key in keys:
                    session_data = self.redis.hgetall(key)
                    if session_data.get('user_id') == user_id:
                        if not project_id or session_data.get('project_id') == project_id:
                            # Parse JSON fields
                            for field in ['conversation_history', 'context', 'preferences']:
                                if field in session_data:
                                    try:
                                        session_data[field] = json.loads(session_data[field])
                                    except (json.JSONDecodeError, TypeError):
                                        session_data[field] = [] if field == 'conversation_history' else {}
                            sessions.append(session_data)
            else:
                # Fallback - this is limited with Django cache
                logger.warning("Redis not available - user session lookup limited")
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful
        """
        try:
            if self.redis:
                result = self.redis.delete(f"session:{session_id}")
                return result > 0
            else:
                cache.delete(f"session:{session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            if self.redis:
                # Redis handles expiration automatically
                pass
            else:
                # Django cache also handles expiration automatically
                pass
                
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
    
    def get_session_stats(self, session_id: str) -> Dict:
        """
        Get session statistics
        
        Args:
            session_id: Session identifier
            
        Returns:
            Statistics dictionary
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return {}
            
            history = session_data.get('conversation_history', [])
            
            stats = {
                'total_messages': len(history),
                'user_messages': len([m for m in history if m.get('role') == 'user']),
                'ai_messages': len([m for m in history if m.get('role') == 'assistant']),
                'session_duration': self._calculate_session_duration(session_data),
                'last_activity': session_data.get('last_activity'),
                'created_at': session_data.get('created_at')
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {}
    
    def _calculate_session_duration(self, session_data: Dict) -> int:
        """Calculate session duration in seconds"""
        try:
            created_at = datetime.fromisoformat(session_data['created_at'])
            last_activity = datetime.fromisoformat(session_data['last_activity'])
            return int((last_activity - created_at).total_seconds())
        except Exception:
            return 0
    
    def search_conversation_history(self, session_id: str, query: str, limit: int = 10) -> List[Dict]:
        """
        Search conversation history
        
        Args:
            session_id: Session identifier
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching messages
        """
        try:
            history = self.get_conversation_history(session_id)
            
            results = []
            query_lower = query.lower()
            
            for message in history:
                content = message.get('content', '').lower()
                if query_lower in content:
                    results.append(message)
                    
                if len(results) >= limit:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching conversation history: {e}")
            return []
    
    def export_session_data(self, session_id: str) -> Optional[Dict]:
        """
        Export complete session data
        
        Args:
            session_id: Session identifier
            
        Returns:
            Complete session data for export
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return None
            
            # Add export metadata
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'session_data': session_data,
                'stats': self.get_session_stats(session_id)
            }
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting session data: {e}")
            return None
    
    def is_connected(self) -> bool:
        """Check if Redis connection is available"""
        try:
            if self.redis:
                self.redis.ping()
                return True
            return False
        except Exception:
            return False


# Global instance
session_memory = SessionMemoryManager()


class ConversationContext:
    """
    Context manager for conversation sessions
    """
    
    def __init__(self, user_id: str, project_id: str, session_type: str = 'conversation'):
        self.user_id = user_id
        self.project_id = project_id
        self.session_type = session_type
        self.session_id = None
        self.memory_manager = session_memory
    
    def __enter__(self):
        """Enter context - create or get session"""
        # Try to find existing session
        existing_sessions = self.memory_manager.get_user_sessions(self.user_id, self.project_id)
        active_session = None
        
        for session in existing_sessions:
            if session.get('session_type') == self.session_type and session.get('state') == 'active':
                active_session = session
                break
        
        if active_session:
            self.session_id = active_session['session_id']
            self.memory_manager.update_session_activity(self.session_id)
        else:
            self.session_id = self.memory_manager.create_session(
                self.user_id, 
                self.project_id, 
                self.session_type
            )
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - update session state"""
        if self.session_id:
            self.memory_manager.update_session_activity(self.session_id)
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add message to conversation"""
        if not self.session_id:
            return False
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        if metadata:
            message.update(metadata)
        
        return self.memory_manager.add_message_to_history(self.session_id, message)
    
    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get conversation history"""
        if not self.session_id:
            return []
        
        return self.memory_manager.get_conversation_history(self.session_id, limit)
    
    def update_context(self, context_updates: Dict):
        """Update session context"""
        if not self.session_id:
            return False
        
        return self.memory_manager.update_session_context(self.session_id, context_updates)
    
    def get_context(self) -> Dict:
        """Get session context"""
        if not self.session_id:
            return {}
        
        return self.memory_manager.get_session_context(self.session_id)
    
    def get_session_id(self) -> str:
        """Get current session ID"""
        return self.session_id