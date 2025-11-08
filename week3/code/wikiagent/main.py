from wikiagent import wiki_agent
import asyncio

agent = wiki_agent.create_agent()
agent_callback = wiki_agent.NamedCallback(agent)


async def run_agent(user_prompt: str = 'where do capybaras live?'):

    results = await agent.run(
        user_prompt=user_prompt,
        event_stream_handler=agent_callback
    )

    return results

def run_agent_sync(user_prompt: str):
    return asyncio.run(run_agent(user_prompt))


result = run_agent_sync('where do capybaras live?')
print('\n\n')
print(result.output.format_article())