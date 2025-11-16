# from wikiagent import wiki_agent
# from wikiagent.agent_logging import log_run, save_log
import wiki_agent
from agent_logging import log_run, save_log
import asyncio



agent = wiki_agent.create_agent()
agent_callback = wiki_agent.NamedCallback(agent)


async def run_agent(user_prompt: str = 'where do capybaras live?'):

    results = await agent.run(
        user_prompt=user_prompt,
        event_stream_handler=agent_callback
    )

    log_entry = log_run(agent, results)
    save_log(log_entry)

    return results

def run_agent_sync(user_prompt: str):
    return asyncio.run(run_agent(user_prompt))


def main():
    result = run_agent_sync('where do capybaras live?')
    print('\n\n')
    print(result.output.format_article())


if __name__ == "__main__":
    main()
