from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

class ResearchConstraints(BaseModel):
    """
    A set of limiting factors or requirements for the research output.
    """
        
    model_config = ConfigDict(extra="forbid") 
    audience: Optional[str] = Field(
        ..., 
        description="The intended target audience (e.g., 'experts', 'beginners'). Return null if not specified."
    )
    depth: Optional[str] = Field(
        ..., 
        description="The level of detail required (e.g., 'high-level overview', 'deep technical dive'). Return null if not specified."
    )
    region: Optional[str] = Field(
        ..., 
        description="The geographic region to focus on (e.g., 'North America', 'Global'). Return null if not specified."
    )
    time_scope: Optional[str] = Field(
        ..., 
        description="The time period relevant to the research (e.g., 'last 5 years', '2023-2024'). Return null if not specified."
    )
    format: Optional[str] = Field(
        ..., 
        description="The desired output format (e.g., 'bullet points', 'whitepaper'). Return null if not specified."
    )

class ResearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid") 
    thought_process: str = Field(
        ..., 
        description="Step-by-step reasoning process to arrive at the solution. Analyze the problem carefully here."
    )
    goal: str = Field(
        ..., 
        description="A concise, 1-sentence summary of the main research objective."
    )
    constraints: ResearchConstraints

class SubQuestion(BaseModel):
    """
    A granular research tasks to achieve the objective
    """
    model_config = ConfigDict(extra="forbid") 
    id: str = Field(
        ..., 
        description="Unique identifier for the question, e.g., 'Q1'"
    )
    description: str = Field(
        ..., 
        description="The specific question or task to be researched"
    )
    priority: int = Field(
        ..., 
        description="Execution order priority (1 = highest/first)"
    )
    dependencies: List[str] = Field(
        ..., 
        description="List of IDs (e.g., ['Q1']) that must be completed before this one"
    )
    suggested_tools: List[str] = Field(
        ..., 
        description="Tools recommended for this task, e.g., ['web_search']"
    )
    notes: str = Field(
        ...,
        description="Any extra context, hints, or constraints for the agent"
    )

class ResearchPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    thought_process: str = Field(
        ..., 
        description="Step-by-step reasoning process to arrive at the solution. Analyze the problem carefully here."
    )
    overall_objective: str = Field(
        ..., 
        description="The main goal of the research session"
    )
    subquestions: List[SubQuestion]
    global_strategy: str = Field(
        ..., 
        description="A high-level paragraph explaining the approach to the problem"
    )

class AgentAction(BaseModel):
    """
    Represents the next action the agent should take and its reasoning.
    """
    model_config = ConfigDict(extra="forbid")
    thought_process: str = Field(
        ..., 
        description="Step-by-step reasoning process to arrive at the solution. Analyze the problem carefully here."
    )
    action: Literal["plan", "execute", "reflect", "synthesize"] = Field(
        ..., 
        description="The specific action the agent has decided to take next."
    )

class SearchQueries(BaseModel):
    """
    A Pydantic model to structure a list of web search queries.
    """
    model_config = ConfigDict(extra="forbid") 
    queries: List[str] = Field(
        ...,
        description="A list of 3–5 focused web search queries for the given subquestion.",
        min_length=3,
        max_length=5
    )
