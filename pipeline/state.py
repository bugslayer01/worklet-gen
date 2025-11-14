from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field

from core.llm.outputs import WorkletGenerationResult
from core.constants import *
from core.models.document import Documents
from core.models.worklet import Worklet, SimpleDomainsKeywords

class AgentState(BaseModel):
    thread_id: str
    count: int
    files: Optional[List[Any]] = None
    links: List[str] = Field(default_factory=list)
    custom_prompt: Optional[str] = None
    parsed_data: Optional[Documents] = None
    generation_output: Optional[WorkletGenerationResult] = None
    keywords_domains: Optional[SimpleDomainsKeywords] = None
    links_data: Optional[list[Dict]] = Field(default_factory=list)
    web_search: Optional[bool] = False
    web_search_results: Optional[Union[Dict, List]] = Field(default_factory=list)
    worklets: Optional[List[Worklet]] = Field(default_factory=list)
