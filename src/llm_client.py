from abc import ABC, abstractmethod
from typing import List, Dict, Any, Iterator, Optional, Callable
from groq import Groq
from openai import OpenAI
import json


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients with memory management."""
    
    def __init__(self, model: str, tools_func: List[Callable] = None, tools_info: List = None, temperature: float = 0.7, max_tokens: int = 1024):
        self.model = model
        self.tools_info = tools_info if tools_info is not None else []
        self.tools_func = {f.__name__: f for f in tools_func} if tools_func is not None else {}
        if len(self.tools_info) != len(self.tools_func):
            raise ValueError("tools_info and tools_func must have the same length")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._memory: List[Dict[str, str]] = []
    
    def set_memory(self, messages: List[Dict[str, str]]) -> None:
        """Set the conversation memory."""
        self._memory = messages.copy()
    
    def get_memory(self) -> List[Dict[str, str]]:
        """Get the current conversation memory."""
        return self._memory.copy()
    
    def add_to_memory(self, cell: Dict[str,str]) -> None:
        """Add a message to the conversation memory."""
        self._memory.append(cell)
    
    def clear_memory(self) -> None:
        """Clear the conversation memory."""
        self._memory.clear()
    
    def get_full_messages(self, user_message: str) -> List[Dict[str, str]]:
        """Get full message list including memory and current user message."""
        messages = self._memory.copy()
        messages.append({"role": "user", "content": user_message})
        return messages
    
    @abstractmethod
    def generate_response(self, message: str, stream: bool = True, reason: bool = False, use_tools: bool = False) -> Iterator[str]:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    def generate_complete_response(self, message: str, reason: bool = False, use_tools: bool = False) -> str:
        """Generate a complete response (non-streaming)."""
        pass



class NVIClient(BaseLLMClient):
    """NVIDIA NIM LLM client implementation."""
    
    def __init__(self, model: str = "qwen/qwen3-235b-a22b",
                 tools_info: List = None, 
                 tools_func: List = None,
                 temperature: float = 0.2, max_tokens: int = 8192, top_p: float = 0.7,
                 api_key: str = "$API_KEY_REQUIRED_IF_EXECUTING_OUTSIDE_NGC"):
        super().__init__(model,tools_func, tools_info, temperature, max_tokens)
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key
        )
        self.top_p = top_p
        self.log = []
    
    def generate_response(self, message: str, stream: bool = True, reason: bool = False, use_tools: bool = False) -> Iterator[str]:
        """Generate a streaming response from NVIDIA NIM."""
        messages = self.get_full_messages(message)
        # print(f"Generating response for message: {messages}")
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            extra_body={"chat_template_kwargs": {"thinking": reason}},
            tools=self.tools_info,
            tool_choice= "auto" if use_tools else "none",
            stream=stream
        )
        
        response_content = ""
        for chunk in completion:
            # Handle reasoning content if available
            reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
            if reasoning:
                yield reasoning
                response_content += reasoning
            
            # Handle regular content
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                response_content += content
                yield content
        
        # Add messages to memory after completion
        self.add_to_memory({'role': 'assistant', 'content': response_content})
    
    def generate_complete_response(self, message: str, reason: bool = False, use_tools: bool = False) -> str:
        """Generate a complete response (non-streaming)."""
        messages = self.get_full_messages(message)

        # print(f"[Generating response for message]: {messages}")
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            extra_body={"chat_template_kwargs": {"thinking": reason}},
            tools=self.tools_info,
            tool_choice= "auto" if use_tools else "none",
            stream=False
        )
        self.log.append(completion)
        print(f"[Completion response]: {completion}")
        response_content = completion.choices[0].message.content
        tool_calls = completion.choices[0].message.tool_calls
        
        if use_tools:
            # If tools are used, we need to handle tool calls
            if tool_calls:
                for tool_call in tool_calls:
                    print(f"[Tool call]: {tool_call}")
                    tool_name = tool_call.function.name
                    tool_args = tool_call.function.arguments
                    # Parse tool_args if it's a string (JSON)
                    if isinstance(tool_args, str):
                        try:
                            tool_args = json.loads(tool_args)
                        except Exception as e:
                            print(f"Error parsing tool_args: {e}")
                            tool_args = {}
                    # Call the corresponding function from tools_func
                    if tool_name in self.tools_func:
                        result = self.tools_func[tool_name](**tool_args)
                        tool_call_id = tool_call.id
                        self.add_to_memory({
                            'role': 'tool',
                            'content': str(result),
                            'tool_call_id': tool_call_id,
                            'name': tool_name
                        })
        # Add messages to memory
        if response_content is not None:
            self.add_to_memory({'role': 'assistant', 'content': response_content})

        
        return (response_content, tool_calls)

    def save_log(self, filename: str) -> None:
        """Save the log to a file."""
        with open(filename, 'w') as f:
            # save to a text file
            for entry in self.log:
                f.write(str(entry) + "\n")

