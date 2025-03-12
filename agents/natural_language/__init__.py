"""
Natural Language Processing Agent

This agent uses Ollama with a LLama 3.2 1B model to translate natural language
queries to specific commands that can be routed to the appropriate agent.
"""

from .agent import NaturalLanguageAgent

# This allows the agent router to automatically discover and load the agent
Agent = NaturalLanguageAgent 