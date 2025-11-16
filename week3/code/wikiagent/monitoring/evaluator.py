import asyncio
import json
import re
from typing import Iterable, List, Optional
from schemas import LLMLogRecord, CheckResult, ToolCall, CheckName, CHECK_DESCRIPTIONS, EvaluationChecklist
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from dotenv import load_dotenv
load_dotenv()
# Flow 
# Requirement
# instruction
# answer relevant

# I need to read the log and pass in LLM to check the criteria

# 1. I need to parse the json log file (process file)
# 2. Insert the log .... (db creation using SQL)
# 3. Evaluate the log and get the results (Evaluator)
# 4. Insert the check results (db creation using SQL)

class Evaluator:
    def evaluate(self, log_id: int, record: LLMLogRecord) -> List[CheckResult]:  # pragma: no cover - interface
        raise NotImplementedError
    

@dataclass
class LLMEvaluator(Evaluator):

    def _load_log(self, record: LLMLogRecord):
        
        doc = json.loads(record.raw_json or "{}")

        tool_calls = []
        for msg in doc.get("messages", []):
                for part in msg.get("parts", []) or []:
                    
                    kind = part.get("part_kind")
                    
                    if kind == 'tool-call':
                        if part["tool_name"] == 'final_result':
                            continue
                        call = ToolCall(
                            name=part.get("tool_name"),
                            args=json.loads(part.get("args"))
                        )
                        tool_calls.append(call)

        return doc, tool_calls

    async def evaluate(self, log_id: int, record: LLMLogRecord) -> List[CheckResult]:
        
        checks: List[CheckResult] = []
        prompt = record.user_prompt or ""
        answer = record.assistant_answer or ""
        instructions = record.instructions or ""
        raw_json = record.raw_json or ""
        tool_calls = record.tool_calls or ""
        # doc, tool_calls = self._load_log(record)

        judge_instructions = self._create_judge_instructions()

        # Agent
        judge = Agent(
            name="judge",
            instructions=judge_instructions,
            model="gpt-5-nano",
            output_type=EvaluationChecklist
        )

        user_prompt = f"""
        <INSTRUCTIONS>{instructions}</INSTRUCTIONS>
        <QUESTION>{prompt}</QUESTION>
        <ANSWER>{answer}</ANSWER>
        <TOOL>{tool_calls}</TOOL>
        <LOG>{raw_json}</LOG>
        """.strip()
        
        # run
        output = await judge.run(user_prompt=user_prompt)
        
        for check in output.output.checklist:
            checks.append(
                CheckResult(
                    log_id=log_id,
                    check_name=check.check_name,
                    passed=check.check_pass,
                    details=check.reasoning
                    )
                )   
        # CheckResult
        return checks


    def _generate_checklist_text(self) -> str:
        """
        Generate formatted checklist text from CHECK_DESCRIPTIONS.
        
        Returns:
            Formatted checklist string
        """


        checklist_items = []
        for check_name in CheckName:
            description = CHECK_DESCRIPTIONS[check_name]
            checklist_items.append(f"- {check_name.value}: {description}")
        return "\n".join(checklist_items)


    def _create_judge_instructions(self) -> str:
        """
        Create judge instructions with checklist.
        
        Returns:
            Complete judge instructions
        """
        return f"""
        Use this checklist to evaluate the quality of an AI agent's answer (<ANSWER>) to a user question (<QUESTION>).
        We also include the entire log (<LOG>) for analysis.

        For each item of the checklist, check if the condition is met. 

        Checklist:

        {self._generate_checklist_text()}

        Output true/false for each check and provide a short explanation for your judgment.
        """.strip()
