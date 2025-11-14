# Transform worklets to match database schema
def transform_worklet(worklet):
    transformed = {
        "worklet_id": worklet["worklet_id"],
        "references": worklet["references"],
        "reasoning": str(worklet.get("reasoning", "") or ""),
    }
    string_attrs = [
        "title",
        "problem_statement",
        "description",
        "challenge_use_case",
        "deliverables",
        "infrastructure_requirements",
        "tech_stack",
    ]
    array_attrs = ["kpis", "prerequisites"]
    object_attrs = ["milestones"]

    for attr in string_attrs:
        transformed[attr] = {"selected_index": 0, "iterations": [worklet[attr]]}
    for attr in array_attrs:
        transformed[attr] = {"selected_index": 0, "iterations": [worklet[attr]]}
    for attr in object_attrs:
        transformed[attr] = {"selected_index": 0, "iterations": [worklet[attr]]}

    return transformed
