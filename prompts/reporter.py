REPORTER_PROMPT = """
Generate a comprehensive research report based on:
Analysis: {analysis}
Code Execution Results: {code_results}
Web Research: {web_research}
Visualization URLs: {visualization_urls}
Sources: {sources}

Format the report in YAML:
```yaml
report:
  executive_summary: |
    <summary>
  detailed_findings:
    - <finding 1>
    - <finding 2>
  recommendations:
    - <recommendation 1>
    - <recommendation 2>
  visualizations:
    - url: <visualization_url>
      description: <description of what the visualization shows>
      type: <type of visualization>
  sources:
    - url: <source_url>
      description: <brief description of the source>
  next_steps:
    - <next step 1>
    - <next step 2>
```
"""
