# import asyncio
# from typing import Any, Dict
# from wikiagent import wiki_agent
# from jaxn import JSONParserHandler, StreamingJSONParser

# from wikiagent.agent_logging import log_run, save_log, log_streamed_run



# class SearchResultArticleHandler(JSONParserHandler):
    
#     def on_field_start(self, path: str, field_name: str) -> None:
#         if field_name == "urls":
#             header_level = path.count('/') + 2
#             print(f"\n\n{'#' * header_level} URLs\n")
    
#     def on_field_end(self, path: str, field_name: str, value: str, parsed_value: Any = None) -> None:
#         if field_name == "keyword" and path == "":
#             print(f"# {value}\n")
        
#         if field_name == "found_answer":
#             print(f"\n\nAns --> {value}\n")
    
#     def on_value_chunk(self, path: str, field_name: str, chunk: str) -> None:
#         if field_name == "content":
#             print(chunk, end="", flush=True)
    
#     def on_array_item_end(self, path: str, field_name: str, item: Dict[str, Any] = None) -> None:
#         if field_name == "urls":
#             print(f"- [{item['title']}]({item['url']})")



# async def main():
#     user_input = "where do capybaras live?"

    
#     agent = wiki_agent.create_agent()
#     agent_callback = wiki_agent.NamedCallback(agent)

#     handler = SearchResultArticleHandler()
#     parser = StreamingJSONParser(handler)

#     previous_text = ""

#     async with agent.run_stream(
#         user_input, event_stream_handler=agent_callback
#     ) as result:
#         async for item, last in result.stream_responses(debounce_by=0.01):
#             for part in item.parts:
#                 if not hasattr(part, "tool_name"):
#                     continue
#                 if part.tool_name != "final_result":
#                     continue

#                 current_text = part.args
#                 delta = current_text[len(previous_text):]
#                 parser.parse_incremental(delta)
#                 previous_text = current_text

#         log_entry = await log_streamed_run(agent, result)
#         save_log(log_entry)



# if __name__ == "__main__":
#     asyncio.run(main())