PLANNER_PROMPT = """
Break down this research query into specific tasks. Return ONLY the YAML structure below, replacing the placeholders with actual values:

Query: {query}

```yaml
tasks:
  - type: web_research
    description: <specific research task>
    parameters:
      search_terms:
        - <specific search term 1>
        - <specific search term 2>
  - type: data_analysis
    description: <specific analysis task>
    parameters:
      data_sources:
        - <specific data source 1>
        - <specific data source 2>
  - type: code_execution
    description: <specific code task>
    parameters:
      code_requirements:
        - <specific requirement 1>
        - <specific requirement 2>
```

Rules:
1. Return ONLY the YAML structure above, nothing else
2. Replace ALL placeholders with specific values
3. Keep the exact same indentation (2 spaces)
4. Each task must have all fields (type, description, parameters)
5. Each parameters field must have its required list (search_terms, data_sources, or code_requirements)

"""
