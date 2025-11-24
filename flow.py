import asyncio
from pocketflow import AsyncFlow
from nodes import ClarifyGoalNode, PlanResearchNode, DecideNode, ExecutePlanNode, SynthesizeNode, SearchWeb, AnswerQuestion

def create_agent_flow():
    """
    Create and connect the nodes to form a complete agent flow.
    
    The flow works like this:
    1. DecideAction node decides whether to search or answer
    2. If search, go to SearchWeb node
    3. If answer, go to AnswerQuestion node
    4. After SearchWeb completes, go back to DecideAction
    
    Returns:
        Flow: A complete research agent flow
    """
    # Create instances of each node
    clarify = ClarifyGoalNode()
    plan = PlanResearchNode()
    decide = DecideNode()
    execute = ExecutePlanNode()
    synthesize = SynthesizeNode()
    search = SearchWeb()
    answer = AnswerQuestion()
    

   # Entry: clarify -> plan
    clarify >> plan
    plan - "decide" >> decide
    execute - "decide" >> decide

    # Connect the nodes
    decide - "execute" >> execute
    decide - "synthesize" >> synthesize
    decide - "plan" >> plan
    decide - "reflect" >> synthesize
    
    # Create and return the flow, starting with the DecideAction node
    return AsyncFlow(start=clarify) 