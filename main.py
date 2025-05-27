import os
from dotenv import load_dotenv
from flow import create_research_flow, create_batch_research_flow
import yaml
from utils.logger import research_logger as logger
import time

# Load environment variables
load_dotenv()

def main():
    # Initialize shared store
    shared = {
        "query": "Analyze the impact of AI on healthcare in the last 5 years",
        "research_results": [],
        "analysis_results": [],
        "visualization_results": [],
        "report_results": [],
        "code_execution_results": [],
        "validation_results": None
    }

    # Create and run the flow
    flow = create_research_flow()
    
    try:
        start_time = time.time()
        logger.log_step("Main", "start", "Starting research flow", shared["query"])
        
        flow.run(shared)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Log completion
        logger.log_completion({
            "query": shared["query"],
            "duration": duration,
            "results": {
                "research": len(shared["research_results"]),
                "code_execution": len(shared["code_execution_results"]),
                "analysis": len(shared["analysis_results"]),
                "visualization": len(shared["visualization_results"]),
                "report": len(shared["report_results"])
            },
            "final_validation": shared["validation_results"]
        })
        
    except Exception as e:
        logger.log_error("Main", e, "Research flow failed")
        raise

def batch_main():
    # Example batch of research queries
    shared = {
        "queries": [
            "Analyze the impact of quantum computing on modern cryptography",
            "Evaluate the effectiveness of current AI safety measures",
            "Research the potential of fusion energy as a sustainable power source"
        ],
        "results": {}
    }
    
    # Create and run the batch flow
    batch_flow = create_batch_research_flow()
    batch_flow.run(shared)
    
    # Print results for each query
    for i, query in enumerate(shared["queries"]):
        print(f"\nResearch Report for Query {i+1}:")
        print("===============================")
        print(f"Query: {query}")
        print(yaml.dump(shared["results"][i], default_flow_style=False))

if __name__ == "__main__":
    # Choose between single query or batch processing
    batch_mode = os.getenv("BATCH_MODE", "false").lower() == "true"
    
    if batch_mode:
        batch_main()
    else:
        main() 