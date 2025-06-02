PLANNER_PROMPT = """
Break down this research query into specific tasks. Return ONLY the YAML structure below:

Query: {query}

Task Types:
1. Web Research: Gather information from the web
2. Data Analysis: Analyze data and find insights
3. Code Execution: Run code for processing or visualization

Return ONLY the YAML structure below:

```yaml
tasks:
  - type: web_research
    description: <what to research>
    parameters:
      search_terms:
        - <search term>
  - type: data_analysis
    description: <what to analyze>
    parameters:
      data_sources:
        - <data source>
  - type: code_execution
    description: <what to code>
    parameters:
      code_requirements:
        - <requirement>
```

Rules:
1. Return ONLY the YAML structure above
2. Include at least one task
3. Each task must have type, description, and parameters
4. Use appropriate parameters for each task type
"""
