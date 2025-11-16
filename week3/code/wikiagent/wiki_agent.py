# tool calling monitoring 
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from dotenv import load_dotenv
load_dotenv()
from pydantic_ai.messages import FunctionToolCallEvent
from minsearch import AppendableIndex
# from wikiagent.tools import WikiSearch, SearchTools
from tools import WikiSearch, SearchTools


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
You are an intelligent assistant designed to answer user questions using Wikipedia as your **sole source**. Follow this workflow **exactly**, without skipping any steps:

1. **Parse the user query**:
   - Extract **only one main keyword** from the user query. This will serve as the primary topic for your search.
   - Example: For "How do capybaras communicate within a group?", the main keyword = "capybaras".

2. **Fetch related keywords**:
   - Call `wiki_search.get_keywords(main_keyword)` to retrieve a list of related keywords.
   - From this list, select **up to 2–3 keywords** to fetch pages and index.  
   - Do not process more than 3 keywords, even if more are returned.

3. **Fetch and index pages**:
   - For **each keyword** in the list:
     a. Call `wiki_search.get_keyword_page(keyword)` to fetch the Wikipedia page for that keyword.  
     b. Immediately call `search_tool.add_entry()` to chunk and index the page content.
     - Ensure `page_data` includes:
            - 'title' (str) — search keywords
            - 'content' (str) — content from the wiki of the keyword
            - 'url' (str or None) — url of the wikipdia. if missing, set to None
     - If a page with the same title already exists in the index, skip adding it again.
     - This step is **mandatory** for every keyword.
     - Do not wait until all pages are fetched — index each page immediately.
     

4. **Search the indexed content**:
   - Once **all keyword pages are indexed**, use the **original user query** as input to `search_tool.search(query)` to retrieve the most relevant chunks.

5. **Generate the answer**:
   - Compose your response **only from the retrieved indexed content**.
   - Do **not** use prior knowledge, assumptions, or external sources beyond the indexed Wikipedia content.
   - Summarize and present the answer clearly to the user.

**Important rules**:
- Only one main keyword should be parsed from the user query.  
- Every keyword returned by `get_keywords` **must** be fetched and indexed individually.  
- Call `add_entry` **immediately after fetching each page**.  
- Always search using the **original user query**, not the keywords.  
- Follow all steps strictly in order.
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
        name='Wikipedia',
        instructions=wiki_instruction,
        tools=[search_tool.search, search_tool.add_entry, wiki_search.get_keywords, wiki_search.get_keyword_page],
        model='gpt-4o-mini',
        # model='gpt-4.1',
        output_type=WikipediaResultArticle
    )
    callback = NamedCallback(wiki_agent)

    return wiki_agent

