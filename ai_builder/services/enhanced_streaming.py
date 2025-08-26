"""
Enhanced streaming service for real-time code generation feedback.
Provides token-by-token streaming similar to modern AI coding assistants.
"""
import json
import time
import logging
from typing import Dict, Any, Callable, Optional, Generator
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class StreamEventType(Enum):
    """Types of events that can be streamed to the frontend"""
    THINKING = "thinking"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    FILE_START = "file_start"
    FILE_CONTENT = "file_content"
    FILE_COMPLETE = "file_complete"
    CODE_TOKEN = "code_token"
    STATUS_UPDATE = "status_update"
    PROGRESS = "progress"
    COMPLETION = "completion"
    ERROR = "error"
    SUGGESTION = "suggestion"
    COMMAND = "command"


@dataclass
class StreamEvent:
    """Represents a single streaming event"""
    type: StreamEventType
    data: Dict[str, Any]
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_sse(self) -> str:
        """Convert to Server-Sent Event format"""
        event_data = {
            "type": self.type.value,
            "timestamp": self.timestamp,
            **self.data
        }
        return f"data: {json.dumps(event_data)}\n\n"


class EnhancedStreamingService:
    """Service for enhanced real-time code streaming"""
    
    def __init__(self):
        self.current_file = None
        self.current_content = ""
        self.files_created = []
        self.total_tokens = 0
        self.start_time = None
        
    def stream_generation(self, generator_func: Callable, *args, **kwargs) -> Generator[str, None, None]:
        """
        Wrap a generator function to provide enhanced streaming.
        
        Args:
            generator_func: The function that generates content
            *args, **kwargs: Arguments to pass to the generator function
            
        Yields:
            SSE formatted events for the frontend
        """
        self.start_time = time.time()
        self.files_created = []
        self.total_tokens = 0
        
        try:
            # Initial thinking phase
            yield StreamEvent(
                StreamEventType.THINKING,
                {"message": "AI is analyzing your request...", "progress": 5}
            ).to_sse()
            
            # Start the generation
            for update in generator_func(*args, **kwargs):
                yield from self._process_update(update)
                
            # Completion event
            yield StreamEvent(
                StreamEventType.COMPLETION,
                {
                    "message": "Project generation completed successfully!",
                    "files_created": len(self.files_created),
                    "total_tokens": self.total_tokens,
                    "duration": time.time() - self.start_time,
                    "progress": 100
                }
            ).to_sse()
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield StreamEvent(
                StreamEventType.ERROR,
                {"message": str(e), "error_type": type(e).__name__}
            ).to_sse()
    
    def _process_update(self, update: Dict[str, Any]) -> Generator[str, None, None]:
        """Process different types of updates from the generator"""
        
        update_type = update.get('type', 'unknown')
        
        if update_type == 'status':
            yield StreamEvent(
                StreamEventType.STATUS_UPDATE,
                {
                    "message": update.get('message', ''),
                    "status": update.get('status', 'processing'),
                    "progress": update.get('progress', 0)
                }
            ).to_sse()
            
        elif update_type == 'file_start':
            self.current_file = update.get('filename')
            self.current_content = ""
            yield StreamEvent(
                StreamEventType.FILE_START,
                {
                    "filename": self.current_file,
                    "path": update.get('path', self.current_file),
                    "language": self._detect_language(self.current_file)
                }
            ).to_sse()
            
        elif update_type == 'file_content_token':
            # Stream individual tokens for real-time typing effect
            token = update.get('token', '')
            self.current_content += token
            self.total_tokens += 1
            
            yield StreamEvent(
                StreamEventType.CODE_TOKEN,
                {
                    "filename": self.current_file,
                    "token": token,
                    "current_length": len(self.current_content),
                    "tokens_per_second": self._calculate_tokens_per_second()
                }
            ).to_sse()
            
        elif update_type == 'file_content_streaming':
            # Batch update for file content
            content = update.get('content', '')
            filename = update.get('filename', self.current_file)
            
            # Split into smaller chunks for smoother streaming
            chunk_size = 50  # characters per chunk
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                yield StreamEvent(
                    StreamEventType.FILE_CONTENT,
                    {
                        "filename": filename,
                        "content": chunk,
                        "progress": update.get('progress', 0)
                    }
                ).to_sse()
                time.sleep(0.01)  # Small delay for visual effect
                
        elif update_type == 'file_created':
            self.files_created.append(update.get('file'))
            yield StreamEvent(
                StreamEventType.FILE_COMPLETE,
                {
                    "filename": update.get('file'),
                    "path": update.get('path'),
                    "size": update.get('size', 0),
                    "progress": update.get('progress', 0)
                }
            ).to_sse()
            
        elif update_type == 'analyzing':
            yield StreamEvent(
                StreamEventType.ANALYZING,
                {
                    "message": update.get('message', 'Analyzing requirements...'),
                    "details": update.get('details', {}),
                    "progress": update.get('progress', 10)
                }
            ).to_sse()
            
        elif update_type == 'planning':
            yield StreamEvent(
                StreamEventType.PLANNING,
                {
                    "message": update.get('message', 'Planning project structure...'),
                    "components": update.get('components', []),
                    "progress": update.get('progress', 20)
                }
            ).to_sse()
            
        elif update_type == 'suggestion':
            yield StreamEvent(
                StreamEventType.SUGGESTION,
                {
                    "message": update.get('message'),
                    "category": update.get('category', 'general')
                }
            ).to_sse()
            
        elif update_type == 'command':
            yield StreamEvent(
                StreamEventType.COMMAND,
                {
                    "command": update.get('command'),
                    "description": update.get('description'),
                    "required": update.get('required', False)
                }
            ).to_sse()
    
    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename"""
        if not filename:
            return "text"
            
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascriptreact',
            '.tsx': 'typescriptreact',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.md': 'markdown',
            '.txt': 'plaintext',
            '.sh': 'shellscript',
            '.dockerfile': 'dockerfile',
            '.sql': 'sql',
            '.env': 'dotenv'
        }
        
        for ext, lang in ext_map.items():
            if filename.lower().endswith(ext):
                return lang
                
        # Special cases
        if filename.lower() == 'dockerfile':
            return 'dockerfile'
        if filename.lower() == '.gitignore':
            return 'ignore'
            
        return 'plaintext'
    
    def _calculate_tokens_per_second(self) -> float:
        """Calculate current token generation rate"""
        if not self.start_time or self.total_tokens == 0:
            return 0.0
            
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            return self.total_tokens / elapsed
        return 0.0


class StreamingProgressTracker:
    """Track and report granular progress during generation"""
    
    def __init__(self, total_steps: int = 100):
        self.total_steps = total_steps
        self.current_step = 0
        self.phase_weights = {
            'analyzing': 10,
            'planning': 10,
            'generating': 70,
            'finalizing': 10
        }
        self.current_phase = 'analyzing'
        self.phase_progress = {}
        
    def update_phase(self, phase: str, progress: float = 0) -> float:
        """Update progress for current phase"""
        self.current_phase = phase
        self.phase_progress[phase] = min(progress, 100)
        
        # Calculate overall progress
        total_progress = 0
        cumulative_weight = 0
        
        for p, weight in self.phase_weights.items():
            if p in self.phase_progress:
                total_progress += (self.phase_progress[p] / 100) * weight
            cumulative_weight += weight
            if p == self.current_phase:
                break
                
        return min(total_progress, 100)
    
    def get_detailed_progress(self) -> Dict[str, Any]:
        """Get detailed progress information"""
        return {
            "overall": self.update_phase(self.current_phase, self.phase_progress.get(self.current_phase, 0)),
            "phase": self.current_phase,
            "phase_progress": self.phase_progress.get(self.current_phase, 0),
            "phases_completed": list(self.phase_progress.keys())
        }


def create_streaming_callback(stream_func: Callable[[Dict], None]) -> Callable:
    """
    Create a callback function for use with the smart project generator.
    
    Args:
        stream_func: Function to call with streaming updates
        
    Returns:
        Callback function compatible with smart_project_generator
    """
    progress_tracker = StreamingProgressTracker()
    
    def callback(update: Dict[str, Any]):
        """Enhanced callback with progress tracking"""
        
        # Add progress tracking
        if 'status' in update:
            status = update['status']
            progress = update.get('progress', 0)
            
            if status == 'analyzing':
                overall_progress = progress_tracker.update_phase('analyzing', progress * 5)
            elif status == 'generating':
                overall_progress = progress_tracker.update_phase('generating', progress)
            elif status == 'completed':
                overall_progress = progress_tracker.update_phase('finalizing', 100)
            else:
                overall_progress = progress_tracker.get_detailed_progress()['overall']
                
            update['overall_progress'] = overall_progress
            update['progress_details'] = progress_tracker.get_detailed_progress()
        
        # Stream the update
        stream_func(update)
    
    return callback