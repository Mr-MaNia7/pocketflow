from pocketflow import Flow
from nodes import (
    PlannerNode,
    WebResearchNode,
    DataAnalysisNode,
    VisualizationNode,
    ReporterNode,
    SupervisorNode,
    CodeExecutorNode
)

def create_research_flow():
    """Create and return the research analysis flow."""
    
    # Create nodes
    planner = PlannerNode()
    web_research = WebResearchNode()
    code_executor = CodeExecutorNode()
    data_analysis = DataAnalysisNode()
    visualization = VisualizationNode()
    reporter = ReporterNode()
    supervisor = SupervisorNode()
    
    # Connect nodes
    planner >> web_research
    web_research - "default" >> web_research  # Continue with next task
    web_research - "next" >> code_executor
    code_executor - "default" >> code_executor  # Continue with next task
    code_executor - "next" >> data_analysis
    data_analysis >> visualization >> reporter >> supervisor
    
    # Add revision path
    supervisor - "needs_revision" >> planner
    
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