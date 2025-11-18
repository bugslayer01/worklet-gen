from __future__ import annotations
from typing import List, Literal, Optional
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
    problem_statement: str = Field(..., description="Problem statement of the project idea (28-33 words)")
    description: str = Field(..., description="Description of the project idea (providing context/background, max 100 words)")
    challenge_use_case: str = Field(..., description="Specific challenge or use case addressed by the project idea")
    deliverables: str = Field(..., description="Expected deliverables of the project idea")
    kpis: List[str] = Field(..., description="Key Performance Indicators (KPIs) for the project idea")
    prerequisites: List[str] = Field(..., description="Prerequisites for undertaking the project idea")
    infrastructure_requirements: str = Field(..., description="Infrastructure requirements for the project idea")
    tech_stack: str = Field(..., description="Tentative technology stack for the project idea")
    milestones: dict = Field(..., description="Milestones for the project idea over a 6-month period")
    
class WorkletGenerationResult(BaseModel):
    worklets: List[Worklet]
    web_search: bool = Field(False, description="Indicates if web search is needed for extra information")
    web_search_queries: Optional[List[str]] = Field(default_factory=list, description="List of web search queries to be performed if web_search is True")

class ReferenceKeywordResult(BaseModel):
    google_scholar_keyword: str = Field(..., description="The generated keyword or phrase for searching relevant academic papers on Google Scholar")
    github_keyword: str = Field(..., description="The generated keyword or phrase for searching relevant GitHub repositories")

class ReferenceSortingResult(BaseModel):
    sorted_indices: List[int] = Field(..., description="List of indices representing the sorted order of references (0-indexed) based on relevance")