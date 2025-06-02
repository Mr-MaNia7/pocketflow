VALIDATION_PROMPT = """
Review this research report and determine if it meets quality standards:
{final_report}

Return your decision in YAML format:
```yaml
decision:
  approved: true/false
  feedback: <feedback if not approved>
  confidence: <0-1>
```
"""

CODE_EXECUTION_NEEDS_PROMPT = """
Based on the analysis results, determine if code execution is needed for data processing or other tasks:
{analysis}

Return your decision in YAML format:
```yaml
decision:
  needs_code: true/false
  reason: <explanation>
```
"""
