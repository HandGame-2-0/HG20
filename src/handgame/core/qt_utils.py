"""
Small, shared Qt tools for safely terminating threads.

QThread.wait() blocks the calling thread without flushing its event loop.
When the worker’s termination depends on a cross-thread QueuedConnection
(worker.finished → thread.quit), a standard wait(timeout_ms) in the main thread
will not allow this queue to execute – wait() always waits for the full
timeout, even though the worker finished its work long ago. wait_for_thread_stopped()
alternates between flushing events and checking the thread, so the shutdown completes
as quickly as the worker actually takes to stop.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QCoreApplication, QThread


def wait_for_thread_stopped(thread: QThread, timeout_ms: int, poll_ms: int = 10) -> bool:
    """Waits for `thread` to actually stop, flushing events in the process
    (so that queued thread.quit() calls have a chance to execute).

    Returns True if the thread stopped before the timeout expires.
    """
    deadline = time.monotonic() + (timeout_ms / 1000.0)
    while thread.isRunning():
        QCoreApplication.processEvents()
        if thread.wait(poll_ms):
            return True
        if time.monotonic() >= deadline:
            return False
    return True
