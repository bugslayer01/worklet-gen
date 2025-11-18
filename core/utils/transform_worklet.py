from typing import Dict, Any

from core.utils.worklet_store import build_initial_iteration


# Transform worklets to match database schema with iteration container
def transform_worklet(worklet: Dict[str, Any]) -> Dict[str, Any]:
    base_iteration = build_initial_iteration(worklet)

    transformed = {
        "worklet_id": worklet["worklet_id"],
        "selected_iteration_index": 0,
        "iterations": [base_iteration],
    }

    return transformed
