import asyncio
from dataclasses import dataclass

import wiki_agent
from agent_logging import log_run, save_log


# ============================================================
# Guardrail Data and Exception
# ============================================================

@dataclass
class GuardrailFunctionOutput:
    output_info: str
    tripwire_triggered: bool


class GuardrailException(Exception):
    def __init__(self, message: str, info: GuardrailFunctionOutput):
        super().__init__(message)
        self.info = info


# ============================================================
# Agent Runner
# ============================================================

async def run_agent(agent, user_prompt: str):
    """Run the agent normally, but async."""
    agent_callback = wiki_agent.NamedCallback(agent)

    results = await agent.run(
        user_prompt=user_prompt,
        event_stream_handler=agent_callback
    )

    # Optional logging — enable if needed
    # log_entry = log_run(agent, results)
    # save_log(log_entry)

    return results


# ============================================================
# Guardrail
# ============================================================

async def guardrail(user_prompt: str):
    """
    Guardrail checks whether the prompt is about capybaras.
    If not, it raises GuardrailException.
    """
    print('[guardrail] start')
    await asyncio.sleep(0.5)  # simulate async guardrail work

    text = user_prompt.lower()
    if "capybara" not in text and "capybaras" not in text:
        info = GuardrailFunctionOutput(
            output_info="check fails",
            tripwire_triggered=True,
        )
        print('[guardrail] stop')
        raise GuardrailException("Guardrail triggered: not a capybara question", info)

    info = GuardrailFunctionOutput(
        output_info="check passed",
        tripwire_triggered=False,
    )
    print('[guardrail] stop')
    return info


# ============================================================
# Guardrail-Orchestrated Runner
# ============================================================

async def run_with_guardrails(agent_coroutine, guardrails):
    """
    Run the agent in parallel with one or more guardrails.
    If any guardrail raises GuardrailException, cancel the agent.
    """

    agent_task = asyncio.create_task(agent_coroutine)
    guard_tasks = [asyncio.create_task(g) for g in guardrails]

    try:
        await asyncio.gather(agent_task, *guard_tasks)
        return agent_task.result()

    except GuardrailException as e:
        print("[guardrail fired]", e.info)

        # Cancel agent
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            print("[run_with_guardrails] agent cancelled")

        # Cancel guardrails
        for t in guard_tasks:
            t.cancel()
        await asyncio.gather(*guard_tasks, return_exceptions=True)

        raise


# ============================================================
# Main Entry
# ============================================================

async def main():
    agent = wiki_agent.create_agent()

    # Choose your test case:
    user_prompt = "where do capybaras live?"
    # user_prompt = "where do lions live?"

    result = await run_with_guardrails(
        run_agent(agent, user_prompt),
        [guardrail(user_prompt)]
    )

    print("\n\n")
    print(result.output.format_article())


if __name__ == "__main__":
    asyncio.run(main())