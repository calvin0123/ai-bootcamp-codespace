from dataclasses import dataclass
from enum import Enum
from decimal import Decimal

from pydantic import BaseModel, Field
from enum import Enum
from typing import Iterable, List, Optional


class CheckName(str, Enum):
    instructions_follow = "instructions_follow"
    answer_relevant = "answer relevant"
    # instructions_avoid = "instructions_avoid"
    # answer_clear = "answer_clear"
    # answer_match = "answer_match"
    # answer_citations = "answer_citations"
    # completeness = "completeness"
    # tool_call_search = "tool_call_search"


@dataclass
class CheckResult:
    log_id: int
    check_name: CheckName
    passed: Optional[bool] = None
    # score: Optional[float] = None
    details: Optional[str] = None

@dataclass
class LLMLogRecord:
    filepath: str
    agent_name: Optional[str]
    provider: Optional[str]
    model: Optional[str]
    user_prompt: Optional[str]
    instructions: Optional[str]
    tool_calls: Optional[str]
    total_input_tokens: Optional[int]
    total_output_tokens: Optional[int]
    assistant_answer: Optional[str]
    raw_json: Optional[str]
    # Cost fields represented as Decimal in code
    # input_cost: Optional[Decimal] = None
    # output_cost: Optional[Decimal] = None
    # total_cost: Optional[Decimal] = None


@dataclass
class ToolCall:
    name: str
    args: dict



CHECK_DESCRIPTIONS = {
    CheckName.instructions_follow: "The agent followed the user's instructions (in <INSTRUCTIONS>)",
    CheckName.answer_relevant: "The response directly addresses the user's question",

}

class EvaluationCheck(BaseModel):
    """Single evaluation check result."""
    check_name: CheckName = Field(description="The type of evaluation check")
    reasoning: str = Field(description="The reasoning behind the check result")
    check_pass: bool = Field(description="Whether the check passed (True) or failed (False)")


class EvaluationChecklist(BaseModel):
    """Complete evaluation checklist with all checks."""
    checklist: list[EvaluationCheck] = Field(description="List of all evaluation checks")
    summary: str = Field(description="Evaluation summary")