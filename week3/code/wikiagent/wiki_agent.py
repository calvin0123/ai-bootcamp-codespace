# tool calling monitoring 
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from dotenv import load_dotenv
load_dotenv()
from pydantic_ai.messages import FunctionToolCallEvent
from minsearch import AppendableIndex
from wikiagent.tools import WikiSearch, SearchTools


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
    



wiki_instruction = """
You are an intelligent assistant that answers user queries using Wikipedia as a source.


### Follow this workflow strictly:
1. Parse the main keyword from the user query.
2. Call `wiki_search.get_keywords` to get **all related keywords**.
3. For each keyword in the returned list:
   a. Call `wiki_search.get_keyword_page` to fetch the page for that keyword.
   b. Call `search_tool.add_entry` to chunk and index the page content.
4. After all keywords are processed and indexed, call `search_tool.search` to find relevant chunks.
5. Return the answer based only on the indexed content.

### Notes:
- `get_keyword_page` is called **one keyword at a time**.
- The agent must ensure **all keywords** from `get_keywords` are fetched and indexed before performing the final search.
"""

wiki_search = WikiSearch()

index = AppendableIndex(
    text_fields=["title", "content"],
    keyword_fields=["title"]
)
search_tool = SearchTools(index)


class Reference(BaseModel):
    title: str
    url: str

class WikipediaResultArticle(BaseModel):
    found_answer: bool
    keyword: str
    content: str
    urls: list[Reference]

    def format_article(self):
        output = f"# {self.keyword.upper()}\n\n"
        output += f" {self.content}\n\n"
        
        output += "## References\n"
        for url in self.urls:
            
            output += f"- [{url.title}]({url.url})\n"
                
        return output


def create_agent(config = None) -> Agent:

    index = AppendableIndex(
        text_fields=["title", "content"],
        keyword_fields=["title"]
    )
    search_tool = SearchTools(index)


    wiki_agent = Agent(
        name='Wikipeida',
        instructions=wiki_instruction,
        tools=[search_tool.search, search_tool.add_entry, wiki_search.get_keywords, wiki_search.get_keyword_page],
        model='gpt-4o-mini',
        output_type=WikipediaResultArticle
    )
    callback = NamedCallback(wiki_agent)

    return wiki_agent

