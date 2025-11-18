from datetime import datetime
from pydantic import BaseModel, Field
from typing import List


class Reference(BaseModel):
    title: str = Field(..., description="Title of the academic reference or paper")
    link: str = Field(..., description="URL link to the academic reference or paper")
    description: str = Field(
        ...,
        description="Brief description or abstract of the academic reference or paper",
    )
    tag: str = Field(
        ...,
        description="Tag indicating the source of the reference, e.g., 'google', 'scholar'",
    )


class Worklet(BaseModel):
    worklet_id: str = Field(..., description="Unique identifier for the worklet")
    title: str = Field(..., description="Title of the project idea")
    problem_statement: str = Field(
        ..., description="Problem statement of the project idea (min 50 words)"
    )
    description: str = Field(
        ...,
        description="Description of the project idea (providing context/background, max 100 words)",
    )
    reasoning: str = Field(
        "",
        description="LLM's rationale for why this worklet was proposed",
    )
    challenge_use_case: str = Field(
        ..., description="Specific challenge or use case addressed by the project idea"
    )
    deliverables: List[str] = Field(
        ..., description="Expected deliverables of the project idea"
    )
    kpis: List[str] = Field(
        ..., description="Key Performance Indicators (KPIs) for the project idea"
    )
    prerequisites: List[str] = Field(
        ..., description="Prerequisites for undertaking the project idea"
    )
    infrastructure_requirements: str = Field(
        ..., description="Infrastructure requirements for the project idea"
    )
    tech_stack: str = Field(
        ..., description="Tentative technology stack for the project idea"
    )
    milestones: dict = Field(
        ..., description="Milestones for the project idea over a 6-month period"
    )
    references: List[Reference] = Field(
        ...,
        description="List of relevant academic references or papers for the project idea",
    )


class StringAttribute(BaseModel):
    selected_index: int = Field(..., description="Selected index for the attribute")
    iterations: List[str] = Field(
        ..., description="List of iterations for the string attribute"
    )


class ArrayAttribute(BaseModel):
    selected_index: int = Field(..., description="Selected index for the attribute")
    iterations: List[List[str]] = Field(
        ..., description="List of iterations for the array attribute"
    )


class ObjectAttribute(BaseModel):
    selected_index: int = Field(..., description="Selected index for the attribute")
    iterations: List[dict] = Field(
        ..., description="List of iterations for the object attribute"
    )


class TransformedWorklet(BaseModel):
    worklet_id: str = Field(..., description="Unique identifier for the worklet")
    title: StringAttribute = Field(..., description="Transformed title attribute")
    problem_statement: StringAttribute = Field(
        ..., description="Transformed problem statement attribute"
    )
    description: StringAttribute = Field(
        ..., description="Transformed description attribute"
    )
    reasoning: str = Field(
        "",
        description="LLM's rationale for why this worklet was proposed",
    )
    challenge_use_case: StringAttribute = Field(
        ..., description="Transformed challenge use case attribute"
    )
    deliverables: ArrayAttribute = Field(
        ..., description="Transformed deliverables attribute"
    )
    kpis: ArrayAttribute = Field(..., description="Transformed KPIs attribute")
    prerequisites: ArrayAttribute = Field(
        ..., description="Transformed prerequisites attribute"
    )
    infrastructure_requirements: StringAttribute = Field(
        ..., description="Transformed infrastructure requirements attribute"
    )
    tech_stack: StringAttribute = Field(
        ..., description="Transformed tech stack attribute"
    )
    milestones: ObjectAttribute = Field(
        ..., description="Transformed milestones attribute"
    )
    references: List[Reference] = Field(
        ...,
        description="List of relevant academic references or papers for the project idea",
    )


class WorkletIteration(TransformedWorklet):
    iteration_id: str = Field(
        ..., description="Unique identifier for a specific worklet iteration"
    )
    created_at: datetime = Field(
        ..., description="Timestamp indicating when this iteration was created"
    )


class StoredWorklet(BaseModel):
    worklet_id: str = Field(..., description="Unique identifier for the worklet")
    selected_iteration_index: int = Field(
        ..., ge=0, description="Index of the default iteration for this worklet"
    )
    iterations: List[WorkletIteration] = Field(
        ..., description="Ordered list of worklet iterations"
    )


class SimpleDomainsKeywords(BaseModel):
    domains: List[str] = Field(..., description="List of approved domains")
    keywords: List[str] = Field(..., description="List of approved keywords")
