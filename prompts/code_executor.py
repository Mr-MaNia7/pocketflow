CODE_EXECUTION_PROMPT = """
Generate Python code to satisfy these requirements:
Requirements: {code_requirements}
Context from analysis: {analysis}

You MUST return ONLY the following YAML structure, with no additional text or explanations:
```yaml
code: |
    # Your Python code here
    # Must be valid Python code
    # Must include proper imports
    # Must save ALL visualizations to temp_dir using plt.savefig()
    # Example: plt.savefig(os.path.join(temp_dir, 'visualization.png'))
    # Must set 'output' variable with the result
explanation: |
    Brief explanation of what the code does
visualization_type: |
    Type of visualization if applicable, or 'none'
```

Rules:
1. Return ONLY the YAML structure above
2. Do not add any text before or after the YAML
3. The code must be valid Python code
4. The code must save ALL visualizations to temp_dir using plt.savefig()
5. The code must set an 'output' variable
6. Keep the exact same indentation (2 spaces)
7. Do not modify the structure or add/remove fields
"""
