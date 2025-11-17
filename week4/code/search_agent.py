from pydantic_ai import Agent
from pydantic_ai.messages import FunctionToolCallEvent
from pydantic_ai.messages import FunctionToolCallEvent
from pydantic_ai.messages import ModelMessage, UserPromptPart

import search_tools
from dotenv import load_dotenv
load_dotenv()
from pydantic import BaseModel

from dataclasses import dataclass

@dataclass
class AgentConfig:
    chunk_size: int = 2000
    chunk_step: int = 1000
    top_k: int = 5

    model: str = "openai:gpt-4o-mini"


class NamedCallback:

    def __init__(self, agent):
        self.agent_name = agent.name

    async def print_function_calls(self, ctx, event):
        # Detect nested streams
        if hasattr(event, "__aiter__"):
            async for sub in event:
                await self.print_function_calls(ctx, sub)
            return

        if isinstance(event, FunctionToolCallEvent):
            tool_name = event.part.tool_name
            args = event.part.args
            print(f"TOOL CALL ({self.agent_name}): {tool_name}({args})")

    async def __call__(self, ctx, event):
        return await self.print_function_calls(ctx, event)


search_instructions = """
You are a search assistant for the Evidently documentation.

Evidently is an open-source Python library and cloud platform for evaluating, testing, and monitoring data and AI systems.
It provides evaluation metrics, testing APIs, and visual reports for model and data quality.

Your task is to help users find accurate, relevant information about Evidently's features, usage, and integrations.

Requirements:

- For every user query, you must perform at least 3 and at most 6 separate searches
    to gather enough context and verify accuracy.  
- Each search should use a different angle, phrasing, or keyword
    variation of the user's query. 
- Keep all searches relevant to Evidently and centered on technical
    or conceptual details from its documentation.
- After performing all searches, write a concise, accurate answer
    that synthesizes the findings.  
- For each section, include references listing all the sources
    you used to write that section.
- Do not perform more than 6 searches per query.
""".strip()


def force_answer_after_6_searches(messages: list[ModelMessage]) -> list[ModelMessage]: 
    num_tool_calls = 0

    for m in messages:
        for p in m.parts:
            if p.part_kind == 'tool-call' and p.tool_name == 'search':
                num_tool_calls = num_tool_calls + 1

    if num_tool_calls >= 6:
        print('forcing output')
        last_message = messages[-1]
        finish_prompt = 'System message: The maximal number of searches has exceeded 6. Proceed to finishing the writeup'
        finish_prompt_part = UserPromptPart(finish_prompt)
        last_message.parts.append(finish_prompt_part)

    return messages



def create_agent(config: AgentConfig = None) -> Agent:
    if config is None:
        config = AgentConfig()

    tools = search_tools.prepare_search_tools(
        config.chunk_size,
        config.chunk_step,
        config.top_k
    )

    agent = Agent(
        name="search",
        instructions=search_instructions,
        tools=[tools.search, tools.read_file],
        model=config.model,
        output_type=SearchResultArticle,
        history_processors=[force_answer_after_6_searches]
    )

    # print(agent.toolsets[0].tools.keys())

    return agent


class Reference(BaseModel):
    title: str
    filename: str

class Section(BaseModel):
    heading: str
    content: str
    references: list[Reference]


class SearchResultArticle(BaseModel):
    found_answer: bool
    title: str
    sections: list[Section]
    references: list[Reference]

    def format_article(self, base_url: str = "https://github.com/evidentlyai/docs/blob/main"):
        output = f"# {self.title}\n\n"

        for section in self.sections:
            output += f"## {section.heading}\n\n"
            output += f"{section.content}\n\n"
            output += "### References\n"
            for ref in section.references:
                output += f"- [{ref.title}]({base_url}/{ref.filename})\n"

        output += "## References\n"
        for ref in self.references:
            output += f"- [{ref.title}]({base_url}/{ref.filename})\n"

        return output
