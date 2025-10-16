from core.models.worklet import Worklet


def fix_dashes(worklet: Worklet) -> Worklet:
    worklet.title = worklet.title.replace("‑", "-")
    worklet.problem_statement = worklet.problem_statement.replace("‑", "-")
    worklet.description = worklet.description.replace("‑", "-")
    worklet.deliverables = worklet.deliverables.replace("‑", "-")
    worklet.infrastructure_requirements = worklet.infrastructure_requirements.replace(
        "‑", "-"
    )
    for i, kpi in enumerate(worklet.kpis):
        worklet.kpis[i] = kpi.replace("‑", "-")
    for i, prereq in enumerate(worklet.prerequisites):
        worklet.prerequisites[i] = prereq.replace("‑", "-")
    worklet.tech_stack = worklet.tech_stack.replace("‑", "-")
    for milestone, desc in worklet.milestones.items():
        worklet.milestones[milestone] = desc.replace("‑", "-")
    return worklet
