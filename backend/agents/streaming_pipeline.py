"""
Streaming pipeline for progressive response delivery.

This module provides streaming capabilities to deliver partial results
to the user as they become available, improving perceived performance.

Benefits:
- TTFB < 500ms (vs 5-10s for full response)
- User sees progress (intent detected, tools running, etc.)
- Better UX for long-running queries
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional, AsyncIterator
from dataclasses import dataclass, asdict


logger = logging.getLogger(__name__)


@dataclass
class StreamEvent:
    """Event sent via streaming."""
    type: str  # "status", "intent", "tool_result", "analysis", "response_chunk", "complete", "error"
    stage: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_sse(self) -> str:
        """
        Convert to Server-Sent Event format.

        Returns:
            SSE-formatted string

        Examples:
            >>> event = StreamEvent(type="status", stage="intent", message="Analyzing...")
            >>> sse = event.to_sse()
            >>> "data: " in sse
            True
        """
        data = asdict(self)
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


class StreamingQueue:
    """
    Queue for streaming events.

    Allows different parts of the pipeline to emit events that
    will be streamed to the client.
    """

    def __init__(self, max_size: int = 100):
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._closed = False

    async def put(self, event: StreamEvent):
        """Add event to stream."""
        if not self._closed:
            await self.queue.put(event)

    async def get(self) -> Optional[StreamEvent]:
        """Get next event from stream."""
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=30.0)
        except asyncio.TimeoutError:
            return None

    def close(self):
        """Mark stream as closed."""
        self._closed = True

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self.queue.empty()


class StreamingCallback:
    """
    Callback for streaming progress updates.

    Used by pipeline to emit events during execution.
    """

    def __init__(self, queue: StreamingQueue, language: str = "fr"):
        self.queue = queue
        self.language = language
        self.stage_messages = self._get_stage_messages()

    def _get_stage_messages(self) -> Dict[str, Dict[str, str]]:
        """Get localized stage messages."""
        return {
            "intent": {
                "fr": "🔍 Analyse de votre question...",
                "en": "🔍 Analyzing your question..."
            },
            "context": {
                "fr": "📍 Résolution du contexte...",
                "en": "📍 Resolving context..."
            },
            "tools": {
                "fr": "🛠️ Collecte des données football...",
                "en": "🛠️ Collecting football data..."
            },
            "causal": {
                "fr": "🧠 Analyse causale en cours...",
                "en": "🧠 Causal analysis in progress..."
            },
            "analysis": {
                "fr": "📊 Analyse des données...",
                "en": "📊 Analyzing data..."
            },
            "response": {
                "fr": "✍️ Génération de la réponse...",
                "en": "✍️ Generating response..."
            }
        }

    async def __call__(self, stage: str, message: Optional[str] = None, data: Optional[Dict] = None):
        """
        Emit status update.

        Args:
            stage: Current stage (intent, tools, analysis, response)
            message: Optional custom message
            data: Optional data payload
        """
        # Use localized message if not provided
        if message is None:
            stage_msgs = self.stage_messages.get(stage, {})
            message = stage_msgs.get(self.language, f"Processing {stage}...")

        event = StreamEvent(
            type="status",
            stage=stage,
            message=message,
            data=data
        )

        await self.queue.put(event)
        logger.debug(f"Stream event: {stage} - {message}")

    async def emit_intent(self, intent_data: Dict[str, Any]):
        """Emit intent detection result."""
        event = StreamEvent(
            type="intent",
            stage="intent",
            data=intent_data
        )
        await self.queue.put(event)

    async def emit_tool_result(self, tool_name: str, result: Any, error: Optional[str] = None):
        """Emit tool execution result."""
        event = StreamEvent(
            type="tool_result",
            stage="tools",
            data={
                "tool": tool_name,
                "success": error is None,
                "error": error
            }
        )
        await self.queue.put(event)

    async def emit_analysis(self, analysis_data: Dict[str, Any]):
        """Emit analysis result."""
        event = StreamEvent(
            type="analysis",
            stage="analysis",
            data=analysis_data
        )
        await self.queue.put(event)

    async def emit_response_chunk(self, chunk: str):
        """Emit response chunk."""
        event = StreamEvent(
            type="response_chunk",
            stage="response",
            data={"chunk": chunk}
        )
        await self.queue.put(event)

    async def emit_complete(self, final_data: Optional[Dict] = None):
        """Emit completion event."""
        event = StreamEvent(
            type="complete",
            data=final_data
        )
        await self.queue.put(event)

    async def emit_error(self, error_message: str, error_type: Optional[str] = None):
        """Emit error event."""
        event = StreamEvent(
            type="error",
            message=error_message,
            data={"error_type": error_type} if error_type else None
        )
        await self.queue.put(event)


async def stream_generator(queue: StreamingQueue) -> AsyncIterator[str]:
    """
    Generate Server-Sent Events from queue.

    Args:
        queue: Streaming queue

    Yields:
        SSE-formatted strings

    Examples:
        >>> queue = StreamingQueue()
        >>> async for event in stream_generator(queue):
        ...     print(event)
    """
    try:
        while True:
            event = await queue.get()

            if event is None:
                # Timeout or queue closed
                break

            # Yield SSE-formatted event
            yield event.to_sse()

            # Stop if complete or error
            if event.type in ("complete", "error"):
                break

    except Exception as e:
        logger.error(f"Error in stream generator: {e}", exc_info=True)
        error_event = StreamEvent(
            type="error",
            message=f"Stream error: {str(e)}"
        )
        yield error_event.to_sse()

    finally:
        queue.close()


def chunk_text(text: str, chunk_size: int = 50) -> list[str]:
    """
    Split text into chunks for streaming.

    Args:
        text: Text to chunk
        chunk_size: Approximate chunk size in characters

    Returns:
        List of text chunks

    Examples:
        >>> text = "This is a long response that should be chunked."
        >>> chunks = chunk_text(text, chunk_size=10)
        >>> len(chunks) > 1
        True
    """
    if not text:
        return []

    # Split by sentences first
    import re
    sentences = re.split(r'([.!?]\s+)', text)

    chunks = []
    current_chunk = ""

    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        separator = sentences[i + 1] if i + 1 < len(sentences) else ""

        if len(current_chunk) + len(sentence) + len(separator) > chunk_size and current_chunk:
            chunks.append(current_chunk)
            current_chunk = sentence + separator
        else:
            current_chunk += sentence + separator

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
