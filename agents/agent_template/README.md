# Agent Template

This directory contains a template for creating new agents for AgentOS.

## Creating a New Agent

1. Copy this entire directory to a new directory named after your agent:
   ```
   cp -r agent_template my_new_agent
   ```

2. Rename the agent class in `agent.py` from `TemplateAgent` to your agent's name.

3. Update the `__init__.py` file to import and expose your agent class.

4. Implement your agent's functionality in `agent.py`.

5. Create an appropriate `.env.example` file with the environmental variables your agent needs.

6. Update this README.md with information about your agent.

## Agent Implementation Guidelines

### Required Methods

All agents must implement these methods:

- `process(user_input: str)` - Process user input and return results
- `get_capabilities()` - Return a list of capabilities this agent provides
- `summarize_result(result)` - Generate a user-friendly summary of results

### Result Format

Your agent's `process()` method should return a dictionary with this structure:

```python
{
    "status": "success",  # or "error"
    "message": "Human-readable message",  # For display/logging
    "data": {},  # Any structured data from the operation
    "spoke": "Text to be spoken to the user"  # Optional
}
```

### Environment Variables

Store API credentials and configuration in environment variables:

1. Create a `.env.example` file with placeholder values
2. Document required variables in this README
3. Users should copy `.env.example` to `.env` and fill in their values
