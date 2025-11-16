import sys, os
from tests.utils import get_tool_calls
from wikiagent.wiki_agent import WikipediaResultArticle
from wikiagent import main



# # the search tool is invoked
# # the get_page tool is invoked multiple times
# # the reference are inclded 
def test_search_call_is_invoked():
    
    user_prompt = "where do capybaras live?"
    result = main.run_agent_sync(user_prompt)

#     print(result.output.format_article())

    tool_calls = get_tool_calls(result)
    count = sum(1 for call in tool_calls if call.name == "get_keywords")
    assert count >= 1, f"Expected at least 1 get_keywords tool calls, got {count}"


def test_get_page_is_invoked_3_times():
    
    user_prompt = "where do capybaras live?"
    result = main.run_agent_sync(user_prompt)

    tool_calls = get_tool_calls(result)
    count = sum(1 for call in tool_calls if call.name == "get_keyword_page")

    assert count >= 3, f"Expected at least 3 get_keyword_page tool calls, got {count}"


def test_agent_reference():
    
    user_prompt = "where do capybaras live?"
    result = main.run_agent_sync(user_prompt)

    assert len(result.output.urls) > 0, "Expected at least one reference in the article"