import json
from textwrap import dedent

from core.models.worklet import Worklet


def build_worklet_enhancement_prompt(
    worklet: Worklet,
    user_prompt: str,
) -> str:
    """Create a structured prompt for enhancing a complete worklet."""

    payload = worklet.model_dump()
    payload.pop("references", None)
    worklet_snapshot = json.dumps(payload, indent=2)

    prompt = dedent(
        f"""
        You are enhancing an innovation worklet(project idea/problem statement). Revise the provided content according to the user instruction while preserving factual coherence.

        Requirements:
        - Respect the overall intent of the existing worklet.
        - Update every field as needed so the worklet reads as a consistent whole.
        - Ensure text is clear, specific, and free of placeholders or markdown formatting.
        - Keep outputs within practical length (do not exceed ~160 words per field unless the input already exceeds this).
        - Try to apply the user's instruction to all relevant fields.
        - Produce well-structured bullet lists for array fields.
        - Do not fabricate references.

        Current worklet (JSON):
        {worklet_snapshot}

        User instruction:
        {user_prompt}

        Respond strictly as JSON using this shape:
        {{
          "title": string,
          "problem_statement": string,
          "description": string,
          "reasoning": string,
          "challenge_use_case": string,
          "deliverables": string[],
          "kpis": string[],
          "prerequisites": string[],
          "infrastructure_requirements": string,
          "tech_stack": string,
          "milestones": {{ "string": string, ... }}
        }}
        """
    ).strip()

    return prompt
