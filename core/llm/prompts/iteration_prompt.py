import json
from textwrap import dedent

from core.models.worklet import Worklet


def build_iteration_prompt(
    worklet: Worklet,
    field: str,
    field_type_description: str,
    user_prompt: str,
) -> str:
    """Create a structured prompt for the LLM to iterate on a worklet field."""

    worklet_payload = worklet.model_dump()
    del worklet_payload["worklet_id"]
    del worklet_payload["references"]
    worklet_json = json.dumps(worklet_payload, indent=2)

    prompt = dedent(
        f"""
		You are assisting with refining a single field of a structured innovation worklet.

		Requirements:
		- Update only the field named "{field}".
		- Return a value that is {field_type_description}.
		- Keep the output aligned with the overall intent of the worklet and the provided instruction.
		- Do not include explanations, markdown, or additional commentary.

		Current worklet (JSON):
		{worklet_json}

		User instruction:
		{user_prompt}

		Respond strictly in JSON using this shape:
		{{
		  "updated_value": <your updated value for {field}>
		}}
		"""
    ).strip()

    return prompt
