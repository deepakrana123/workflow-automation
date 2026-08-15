def get_ready_steps(
    dag_steps: list,
    completed_steps: set,
    failed_steps: set,
    waiting_steps: set | None = None,
    skipped_steps: set | None = None,
) -> list:
    """
    Return steps whose dependencies are all in completed_steps.

    Skips steps that are already completed, failed, WAITING on a human
    decision, or SKIPPED by a rule-engine branch decision (a step on a
    not-taken branch must never be scheduled).
    """
    waiting_steps = waiting_steps or set()
    skipped_steps = skipped_steps or set()
    ready = []
    for step in dag_steps:
        step_id = step["id"]

        if step_id in completed_steps:
            continue
        if step_id in failed_steps:
            continue
        if step_id in waiting_steps:
            continue
        if step_id in skipped_steps:
            continue

        depends_on = step.get("depends_on", [])
        if all(dep in completed_steps for dep in depends_on):
            ready.append(step)

    return ready
