def get_ready_steps(dag_steps: list, completed_steps: set, failed_steps: set) -> list:
    """
    Return steps whose dependencies are all in completed_steps.
    Skips steps already completed or failed.
    """
    ready = []
    for step in dag_steps:
        step_id = step["id"]

        if step_id in completed_steps:
            continue

        if step_id in failed_steps:
            continue

        depends_on = step.get("depends_on", [])
        if all(dep in completed_steps for dep in depends_on):
            ready.append(step)

    return ready
