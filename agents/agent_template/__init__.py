"""
Template Agent Package

This is a template for creating new agents.
When creating your own agent:
1. Copy this directory to a new directory named after your agent
2. Rename TemplateAgent to YourAgentName
3. Implement your agent's functionality in agent.py
"""

from .agent import TemplateAgent

# This allows the agent router to automatically discover and load the agent
# Change this to your agent class name when creating a new agent
Agent = TemplateAgent
