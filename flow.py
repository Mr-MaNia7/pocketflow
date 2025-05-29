from pocketflow import Flow
from nodes import (
    PlannerNode,
    WebResearchNode,
    DataAnalysisNode,
    ReporterNode,
    SupervisorNode,
    CodeExecutorNode
)

def create_research_flow():
    """Create and return the research analysis flow with supervisor oversight."""
    
    # Create nodes
    planner = PlannerNode()
    web_research = WebResearchNode()
    data_analysis = DataAnalysisNode()
    code_executor = CodeExecutorNode()
    reporter = ReporterNode()
    supervisor = SupervisorNode()
    
    # Connect nodes with supervisor oversight
    # Initial planning
    planner >> supervisor
    
    # Research phase
    supervisor - "research" >> web_research
    web_research >> supervisor
    
    # Analysis phase
    supervisor - "analyze" >> data_analysis
    data_analysis >> supervisor
    
    # Code execution phase (if needed)
    supervisor - "execute_code" >> code_executor
    code_executor >> supervisor
    
    # Final reporting
    supervisor - "report" >> reporter
    reporter >> supervisor
    
    # Revision paths
    supervisor - "needs_revision" >> planner
    supervisor - "complete" >> None  # End the flow
    
    # Create flow starting with planner
    return Flow(start=planner)

def create_batch_research_flow():
    """Create a flow that can handle multiple research tasks in parallel."""
    from pocketflow import BatchFlow
    
    class ResearchBatchFlow(BatchFlow):
        def prep(self, shared):
            # Return a list of research queries to process
            return [{"query": q} for q in shared["queries"]]
    
    # Create the base research flow
    research_flow = create_research_flow()
    
    # Wrap it in a batch flow
    return ResearchBatchFlow(start=research_flow) 