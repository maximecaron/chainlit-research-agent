import asyncio
import chainlit as cl
from typing import Any, Dict, List, Literal
from pocketflow import AsyncNode
from util import call_llm
from util import search_web
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
import yaml

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
    goal: str = Field(
        ..., 
        description="A concise, 1-sentence summary of the main research objective."
    )
    constraints: ResearchConstraints

class ClarifyGoalNode(AsyncNode):
    """Normalize the raw user query into a goal + constraints."""
    async def prep_async(self, shared: Dict[str, Any]) -> str:
        return shared["user_query"]

    async def exec_async(self, user_query: str) -> Dict[str, Any]:
        system = (
            "You are a research planner. Given a raw user question, "
            "normalize it into a research goal and explicit constraints."
        )
        
        user = f"""    User query:
{user_query}
"""
        return await call_llm.call_llm_json_async(system, user, ResearchRequest)

    async def post_async(self, shared: Dict[str, Any], prep_res: str, exec_res: Dict[str, Any]) -> str:
        # Save the goal and constraints in the shared store
        shared["goal"] = exec_res.get("goal")
        shared["constraints"] = exec_res.get("constraints", {}) or {}
        async with cl.Step(name="ClarifyGoalNode", show_input=False) as step:
           step.output = exec_res
        # start with planning after clarification
        return "default"

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
    overall_objective: str = Field(
        ..., 
        description="The main goal of the research session"
    )
    subquestions: List[SubQuestion]
    global_strategy: str = Field(
        ..., 
        description="A high-level paragraph explaining the approach to the problem"
    )

class PlanResearchNode(AsyncNode):
    """Plan / task decomposition stage."""
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "goal": shared.get("goal"),
            "constraints": shared.get("constraints", {}),
        }

    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        system = "You are a senior research planner. Break a research goal into subquestions."
        goal = prep_res["goal"]
        constraints = prep_res["constraints"]

        user = f"""    Goal:
{goal}

Constraints (may be null):
{constraints}

Return a JSON object
"""
        return await call_llm.call_llm_json_async(system, user, ResearchPlan)

    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        shared["plan"] = exec_res
        shared["last_action"] = "plan"
        n = len(exec_res.get("subquestions", []))
        shared["last_observation"] = f"Planned {n} subquestions."
        async with cl.Step(name="PlanResearchNode", show_input=False) as step:
            step.output = exec_res
        return "decide"

class AgentAction(BaseModel):
    """
    Represents the next action the agent should take and its reasoning.
    """
    model_config = ConfigDict(extra="forbid") 
    action: Literal["plan", "execute", "reflect", "synthesize"] = Field(
        ..., 
        description="The specific action the agent has decided to take next."
    )
    reason: str = Field(
        ..., 
        description="A short explanation of the reasoning behind choosing this action."
    )

class DecideNode(AsyncNode):
    """ReAct-style controller node.

    - Thought  = why we choose the next action
    - Action   = which stage to run next
    - Observation = what we observed from the last action
    """
    MAX_STEPS = 8

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        shared.setdefault("steps", 0)
        shared["steps"] += 1

        return {
            "goal": shared.get("goal"),
            "constraints": shared.get("constraints", {}),
            "plan": shared.get("plan", {}),
            "notes": shared.get("notes", {}),
            "reflection": shared.get("reflection", {}),
            "steps": shared["steps"],
            "last_action": shared.get("last_action"),
            "last_observation": shared.get("last_observation"),
        }

    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        if prep_res["steps"] >= self.MAX_STEPS:
            return {
                "action": "synthesize",
                "reason": f"Reached max_steps={self.MAX_STEPS}, forcing synthesis.",
            }

        system = (
            "You are a meta-controller for a research agent using a " 
            "Thought-Action-Observation loop.\n"
            "Pick exactly one next action from: 'plan', 'execute', 'reflect', 'synthesize'."
        )

        user = f"""    Current steps taken: {prep_res['steps']}

Goal:
{prep_res['goal']}

Constraints:
{prep_res['constraints']}

Current plan:
{prep_res['plan']}

Current notes:
{prep_res['notes']}

Current reflection:
{prep_res['reflection']}

Last action: {prep_res.get('last_action')}
Last observation: {prep_res.get('last_observation')}

Return JSON:
{{
  "action": "plan" | "execute" | "reflect" | "synthesize",
  "reason": "short explanation of your reasoning"
}}
"""
        return await call_llm.call_llm_json_async(system, user, AgentAction)

    async def post_async(
        self,
        shared: Dict[str, Any],
        prep_res: Dict[str, Any],
        exec_res: Dict[str, Any],
    ) -> str:
        action: Literal["plan", "execute", "reflect", "synthesize"] = exec_res.get(
            "action", "synthesize"
        )
        reason = exec_res.get("reason", "(no reason)")
        last_action = prep_res.get("last_action") or "(none yet)"
        last_obs = prep_res.get("last_observation") or "(no observation yet)"
        step_idx = prep_res["steps"]

        # High-level mode label (based on last action)
        if last_action and last_action != "(none yet)":
            mode_label = last_action.capitalize()
        else:
            mode_label = "Start"

        # Collapsible ReAct trace step
        async with cl.Step(
            name=f"ReAct step {step_idx} — {mode_label}",
            show_input=False,
        ) as step:
            thought_el = cl.Text(
                name="Thought",
                content=reason,
                display="inline",
            )
            action_el = cl.Text(
                name="Action",
                content=f"Next action: **{action}**\n\nPrevious: `{last_action}`",
                display="inline",
            )
            obs_el = cl.Text(
                name="Observation",
                content=last_obs,
                display="inline",
            )
            step.output = " "
            step.elements = [thought_el, action_el, obs_el]
        return action

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

class ExecutePlanNode(AsyncNode):
    """Execute the research plan: search + summarize per subquestion."""
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "plan": shared.get("plan", {}),
            "goal": shared.get("goal"),
            "constraints": shared.get("constraints", {}),
        }

    async def _generate_search_queries_async(
        self,
        subq: Dict[str, Any],
        goal: str,
        constraints: Dict[str, Any],
    ) -> List[str]:
        system = (
            "You are a search query generator helping a research agent. " 
            "Generate 3–5 focused web search queries for the subquestion."
        )
        user = f"""    Overall goal: {goal}
Constraints: {constraints}

Subquestion:
{subq['description']}

Return JSON:
{{ "queries": ["...", "..."] }}
"""
        res = await call_llm.call_llm_json_async(system, user, SearchQueries)
        queries = res.get("queries", [])
        return queries[:5]

    async def _summarize_subquestion_async(
        self,
        subq: Dict[str, Any],
        goal: str,
        constraints: Dict[str, Any],
        search_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        system = (
            "You are a research summarizer. Given search results, "
            "write a concise answer to the subquestion, with bullet points and source notes."
        )
        user = f"""    Overall goal: {goal}
Constraints: {constraints}
Subquestion: {subq['description']}

Here are search results (JSON):
{search_results}

Write:
- A short paragraph answer
- 3–7 bullet points with key findings
- A short note on source quality / limitations.
Return your answer as plain Markdown text (no JSON).
"""
        summary = await call_llm.call_llm_async(system, user)
        return {
            "subquestion_id": subq["id"],
            "description": subq["description"],
            "summary": summary,
            "sources": search_results,
        }

    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        plan = prep_res["plan"]
        goal = prep_res["goal"]
        constraints = prep_res["constraints"]

        subquestions = plan.get("subquestions", [])
        notes: Dict[str, Any] = {
            "subquestions": [],
            "overall_objective": plan.get("overall_objective"),
        }
        async with cl.Step(name="ExecutePlanNode", show_input=False) as step:
            for subq in subquestions:
                queries = await self._generate_search_queries_async(subq, goal, constraints)
                aggregated: List[Dict[str, Any]] = []
                async with cl.Step(name=f"ExecuteSubquestions {subq['id']}", show_input=True) as step:
                    step.input = subq['description']
                    for q in queries:
                        try:
                            results = search_web.search_web(q)
                            aggregated.extend(results)
                        except Exception as e:  # noqa: BLE001
                            aggregated.append(
                                {"title": "SEARCH_ERROR", "url": "", "snippet": str(e)}
                            )

                    subq_notes = await self._summarize_subquestion_async(subq, goal, constraints, aggregated)
                    notes["subquestions"].append(subq_notes["summary"])
                    step.output = subq_notes

        return notes

    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        shared["notes"] = exec_res
        shared["last_action"] = "execute"
        n = len(exec_res.get("subquestions", []))
        shared["last_observation"] = f"Executed research for {n} subquestions."

        return "decide"

class SynthesizeNode(AsyncNode):
    """Final synthesis / report generation."""
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        print("🌟 Synthesizing final report...")
        return {
            "goal": shared.get("goal"),
            "constraints": shared.get("constraints", {}),
            "notes": shared.get("notes", {}),
            "reflection": shared.get("reflection", {}),
        }

    async def exec_async(self, prep_res: Dict[str, Any]) -> str:
        system = (
            "You are a research writer. Write a clear, structured report based on notes and reflection."
        )
        user = f"""    Goal:
{prep_res['goal']}

Constraints:
{prep_res['constraints']}

Notes (JSON):
{prep_res['notes']}

Reflection (JSON):
{prep_res['reflection']}

Write a report in Markdown with:
- Title
- Short executive summary
- Sections per subquestion
- Integrated discussion that links subquestions
- Brief 'Limitations & Further Work' section reflecting on gaps
Avoid making up citations; base on the provided sources, but you can paraphrase them.
"""
        return await call_llm.call_llm_async(system, user)

    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: str) -> str:
        shared["report"] = exec_res
        shared["last_action"] = "synthesize"
        shared["last_observation"] = "Final report generated."
        return "default"

class SearchWeb(AsyncNode):
    async def prep_async(self, shared):
        """Get the search query from the shared store."""
        return shared["search_query"]
        
    async def exec_async(self, search_query):
        """Search the web for the given query."""
        # Call the search utility function
        print(f"🌐 Searching the web for: {search_query}")
        results = search_web.search_web_duckduckgo(search_query)
        return results
    
    async def post_async(self, shared, prep_res, exec_res):
        """Save the search results and go back to the decision node."""
        # Add the search results to the context in the shared store
        previous = shared.get("context", "")
        shared["context"] = previous + "\n\nSEARCH: " + shared["search_query"] + "\nRESULTS: " + exec_res
        
        print(f"📚 Found information, analyzing results...")
        
        # Always go back to the decision node after searching
        return "decide"

class AnswerQuestion(AsyncNode):
    async def prep_async(self, shared):
        """Get the question and context for answering."""
        return shared["user_query"], shared.get("context", "")
        
    async def exec_async(self, inputs):
        """Call the LLM to generate a final answer."""
        question, context = inputs
        
        print(f"✍️ Crafting final answer...")
        
        # Create a prompt for the LLM to answer the question
        prompt = f"""
### CONTEXT
Based on the following information, answer the question.
Question: {question}
Research: {context}

## YOUR ANSWER:
Provide a comprehensive answer using the research results.
"""
        # Call the LLM to generate an answer
        answer = await call_llm.call_llm_async(prompt)
        return answer
    
    async def post_async(self, shared, prep_res, exec_res):
        """Save the final answer and complete the flow."""
        # Save the answer in the shared store
        shared["answer"] = exec_res
        
        print(f"✅ Answer generated successfully")
        
        # We're done - no need to continue the flow
        return "done" 