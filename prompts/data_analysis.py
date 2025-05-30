DATA_ANALYSIS_PROMPT = """
Analyze these research results and extract structured data. Return the following YAML with both qualitative and quantitative analysis (if possible):

Research Results: {research_results}

```yaml
analysis:
  key_findings:
    - <finding 1>
    - <finding 2>
  implications:
    - <implication 1>
    - <implication 2>

  metrics:
    - name: <metric name>
      value: <numeric value>
      unit: <unit of measurement>
      source: <where this metric came from>
      confidence: <0-1>

  categories:
    - name: <category name>
      items:
        - name: <item name>
          count: <number of occurrences>
          percentage: <percentage of total>

  time_series:
    - year: <year>
      metrics:
        - name: <metric name>
          value: <value>

  relationships:
    - from: <entity 1>
      to: <entity 2>
      type: <relationship type>
      strength: <0-1>

  data_quality:
    completeness: <0-1>
    reliability: <0-1>
    sources_used: <number>

  visualizations:
    - type: <chart type>
      data_source: <which data to use>
      purpose: <what it shows>
      priority: <1-5>

  next_steps:
    - <suggested next step 1>
    - <suggested next step 2>
```

Rules:
1. `analysis` is required while the rest of the fields are optional.
2. Extract ALL possible numerical and/or qualitative data from the research
3. Create categories where patterns emerge
4. Identify time-based trends if present
5. Note relationships between entities
6. Assess data quality
7. Recommend appropriate visualizations
8. Only include sections where data is available
9. Use consistent units and formats
10. Strictly follow the provided YAML structure
11. Do not add any additional text or explanations outside the YAML
"""
