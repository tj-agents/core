def resolved_route(host, parameters):
    tags = set(parameters.get("tags", []))
    if tags & {"architecture", "review", "security"}:
        lane = "L1"
    elif parameters.get("verifiability") == "compiler":
        lane = "L3"
    else:
        lane = "L2"
    routes = {
        "L1": ("opus", "high", "gpt-5.6-sol", "high"),
        "L2": ("sonnet", "medium", "gpt-5.6-terra", "medium"),
        "L3": ("haiku", "low", "gpt-5.6-luna", "low"),
    }
    model, effort, codex_model, codex_effort = routes[lane]
    return {
        "lane": lane,
        "model": model,
        "effort": effort,
        "codex_model": codex_model,
        "codex_effort": codex_effort,
    }
