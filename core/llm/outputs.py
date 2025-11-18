from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class Sources(BaseModel):
    worklet: List[str]
    link: List[str]
    custom_prompt: List[str]


class KeywordsExtractionResult(BaseModel):
    keywords: Sources
    domains: Sources


class Worklet(BaseModel):
    title: str = Field(..., description="Title of the project idea")
    problem_statement: str = Field(
        ..., description="Problem statement of the project idea (min 50 words)"
    )
    description: str = Field(
        ...,
        description="Description of the project idea (providing context/background, max 100 words)",
    )
    reasoning: str = Field("", description="LLM's rationale for proposing this worklet")
    challenge_use_case: str = Field(
        ...,
        description="Atleast 2 relevant use cases or scenarios addressed by the project idea",
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
    milestones: dict = Field(..., description="Milestones for the project idea")


class WebSearchQueryResult(BaseModel):
    web_search_queries: List[str] = Field(
        ...,
        description="Ordered list of queries the agent should run during web search",
    )


class WorkletGenerationResult(BaseModel):
    worklets: List[Worklet]


class ReferenceKeywordResult(BaseModel):
    google_scholar_keyword: str = Field(
        ...,
        description="The generated keyword or phrase for searching relevant academic papers on Google Scholar",
    )
    github_keyword: str = Field(
        ...,
        description="The generated keyword or phrase for searching relevant GitHub repositories",
    )


class ReferenceSortingResult(BaseModel):
    sorted_indices: List[int] = Field(
        ...,
        description="List of indices representing the sorted order of references (0-indexed) based on relevance",
    )
