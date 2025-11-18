from pydantic import BaseModel, Field
from typing import List

class Reference(BaseModel):
    title: str = Field(..., description="Title of the academic reference or paper")
    link: str = Field(..., description="URL link to the academic reference or paper")
    description: str = Field(..., description="Brief description or abstract of the academic reference or paper")
    tag: str = Field(..., description="Tag indicating the source of the reference, e.g., 'google', 'scholar'")

class Worklet(BaseModel):
    worklet_id: str = Field(..., description="Unique identifier for the worklet")
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
    references: List[Reference] = Field(..., description="List of relevant academic references or papers for the project idea")

class SimpleDomainsKeywords(BaseModel):
    domains: List[str] = Field(..., description="List of approved domains")
    keywords: List[str] = Field(..., description="List of approved keywords")