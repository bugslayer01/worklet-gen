"""
Global broadcasting infrastructure for continuous socket message emission.
This module provides a centralized way to broadcast status messages that repeat
every second until a new message is set.
"""

import asyncio
from app.socket_handler import sio

# Global broadcasting infrastructure
_current_message = {"message": "Initializing pipeline..."}
_broadcast_task = None
_stop_broadcast = asyncio.Event()
_emit_topic = None


async def _broadcast_message():
    """Continuously broadcast the current message every 1 second."""
    global _current_message, _stop_broadcast, _emit_topic
    while not _stop_broadcast.is_set():
        if _emit_topic:
            await sio.emit(_emit_topic, _current_message)
        try:
            await asyncio.wait_for(_stop_broadcast.wait(), timeout=0.5)
        except asyncio.TimeoutError:
            pass


async def update_message(new_message: dict, topic: str = None):
    """
    Update the current message and restart broadcasting.

    Args:
        new_message: Dictionary containing the message to broadcast
        topic: Socket topic to emit to (e.g., "{thread_id}/status_update")
    """
    global _current_message, _broadcast_task, _stop_broadcast, _emit_topic
    _current_message = new_message
    if topic:
        _emit_topic = topic
    if _broadcast_task and not _broadcast_task.done():
        _stop_broadcast.set()
        await _broadcast_task
        _stop_broadcast.clear()
    _broadcast_task = asyncio.create_task(_broadcast_message())


async def stop_broadcasting():
    """Stop the continuous broadcasting."""
    global _broadcast_task, _stop_broadcast
    if _broadcast_task and not _broadcast_task.done():
        _stop_broadcast.set()
        await _broadcast_task
