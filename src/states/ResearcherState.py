import operator
from typing import Annotated, TypedDict, List
from typing_extensions import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, StateGraph
from src.modules.Link import Link
from src.modules.Thought import Thought
from langchain_core.messages import BaseMessage
from states.MainState import MainState


class ResearcherState(MainState):

    products: list[str]
