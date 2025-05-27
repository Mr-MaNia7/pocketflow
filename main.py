import os
from dotenv import load_dotenv
from flow import create_research_flow, create_batch_research_flow
import yaml

# Load environment variables
load_dotenv()

def main():
    # Example research query
    shared = {
        "query": "Analyze the impact of quantum computing on modern cryptography",
        "results": {}
    }
    
    # Create and run the flow
    research_flow = create_research_flow()
    research_flow.run(shared)
    
    # Print results
    print("\nFinal Research Report:")
    print("=====================")
    print(yaml.dump(shared["final_report"], default_flow_style=False))

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