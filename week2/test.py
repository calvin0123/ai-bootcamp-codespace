from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from toyaikit.chat.interface import StdOutputInterface
from toyaikit.chat.runners import PydanticAIRunner

from dotenv import load_dotenv
load_dotenv()

mcp_client = MCPServerStdio(
    command="uv",
    args=["run", "python", "main.py"],
    cwd="mcp_faq"
)


developer_prompt = """
You're a course teaching assistant. 
You're given a question from a course student and your task is to answer it.

If you want to look up the answer, explain why before making the call. Use as many 
keywords from the user question as possible when making first requests.

Make multiple searches. Try to expand your search by using new keywords based on the results you
get from the search.

At the end, make a clarifying question based on what you presented and ask if there are 
other areas that the user wants to explore.
""".strip()


agent = Agent(
    name="faq_agent",
    instructions=developer_prompt,
    toolsets=[mcp_client],
    model='gpt-4o-mini'
)


chat_interface = StdOutputInterface()
runner = PydanticAIRunner(
    chat_interface=chat_interface,
    agent=agent
)


if __name__ == "__main__":
    import asyncio
    asyncio.run(runner.run())