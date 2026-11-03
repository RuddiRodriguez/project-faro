PROMPT_CACHE_MARKING = "##CACHE_HERE##"


# These are the only options supported by OpenAI.
def explicit_prompt_cache_breakpoint() -> dict[str, str]:
    return {"mode": "explicit"}


def explicit_prompt_cache_options() -> dict[str, str]:
    return {"mode": "explicit"}
