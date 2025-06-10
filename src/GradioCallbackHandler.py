from llama_index.core.callbacks.base import BaseCallbackHandler
from llama_index.core.callbacks.schema import CBEventType, EventPayload
from queue import Queue
from typing import Any, Dict, List

class GradioCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming agent events to a Gradio UI."""

    def __init__(self, event_queue: Queue):
        """
        Initializes the callback handler with a queue.

        Args:
            event_queue (Queue): The queue to put event messages into.
        """
        # We need to specify which events we want to listen for.
        # This is a comprehensive list for demonstration.
        super().__init__(event_types=[
            CBEventType.AGENT_STEP,
            CBEventType.TOOL,
            CBEventType.LLM,
        ])
        self.queue = event_queue

    def on_event_start(
        self,
        event_type: CBEventType,
        payload: Dict[str, Any] = None,
        event_id: str = "",
        **kwargs: Any,
    ) -> None:
        """Called when an event starts."""
        # For this example, we'll focus on the end of events to get results.
        # But you could log the start of an action here.
        if event_type == CBEventType.AGENT_STEP:
            # An agent is about to take a step, we can get its thoughts.
            # The payload contains the reasoning.
            if EventPayload.THOUGHTS in payload:
                # The agent might have multiple thoughts in a step
                thoughts = payload[EventPayload.THOUGHTS]
                message = {
                    "type": "thought",
                    "content": thoughts,
                }
                self.queue.put(message)


    def on_event_end(
        self,
        event_type: CBEventType,
        payload: Dict[str, Any] = None,
        event_id: str = "",
        **kwargs: Any,
    ) -> None:
        """Called when an event ends."""
        if event_type == CBEventType.TOOL:
            # A tool has just finished running.
            tool_name = payload.get(EventPayload.TOOL, {}).name
            tool_output = payload.get(EventPayload.TOOL_OUTPUT, "")

            message = {
                "type": "tool_end",
                "tool_name": tool_name,
                "tool_output": str(tool_output),
            }
            self.queue.put(message)

    # We don't need to implement these for this use case
    def start_trace(self, trace_id: str = None) -> None:
        pass

    def end_trace(
        self,
        trace_id: str = None,
        trace_map: Dict[str, List[str]] = None,
    ) -> None:
        pass