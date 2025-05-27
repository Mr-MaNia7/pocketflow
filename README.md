# AI-Powered Research and Analysis System

A sophisticated research system that uses multiple AI agents to perform complex research tasks, with human-in-the-loop validation.

## Features

- Task decomposition of complex research queries
- Specialized AI agents for different aspects of research
- Web research capabilities
- Data analysis and synthesis
- Visualization generation
- Code execution
- Comprehensive reporting
- Quality supervision
- Human-in-the-loop validation
- Batch processing support

## Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd <repository-name>
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   Create a `.env` file with the following:

```
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
BATCH_MODE=false  # Set to true for batch processing
```

## Usage

### Single Query Mode

```python
from flow import create_research_flow

# Create the flow
research_flow = create_research_flow()

# Run with a single query
shared = {
    "query": "Analyze the impact of quantum computing on modern cryptography",
    "results": {}
}
research_flow.run(shared)

# Access results
print(shared["final_report"])
```

### Batch Mode

```python
from flow import create_batch_research_flow

# Create the batch flow
batch_flow = create_batch_research_flow()

# Run with multiple queries
shared = {
    "queries": [
        "Analyze the impact of quantum computing on modern cryptography",
        "Evaluate the effectiveness of current AI safety measures",
        "Research the potential of fusion energy as a sustainable power source"
    ],
    "results": {}
}
batch_flow.run(shared)

# Access results for each query
for i, query in enumerate(shared["queries"]):
    print(f"Results for query {i+1}:")
    print(shared["results"][i])
```

## Project Structure

```
.
├── main.py              # Main entry point
├── nodes.py            # Node definitions
├── flow.py             # Flow definitions
├── requirements.txt    # Project dependencies
├── utils/
│   └── llm.py         # LLM utility wrapper
└── README.md          # This file
```

## Architecture

The system uses PocketFlow's graph-based architecture with the following components:

1. **Planner Node**: Decomposes complex queries into subtasks
2. **Web Research Node**: Gathers information from the web
3. **Data Analysis Node**: Processes and synthesizes information
4. **Visualization Node**: Creates charts and diagrams
5. **Reporter Node**: Generates comprehensive reports
6. **Supervisor Node**: Monitors and validates results

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License
