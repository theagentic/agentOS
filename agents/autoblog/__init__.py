"""
Autoblog Agent Package

This agent automatically generates blog posts from GitHub repositories.
"""

from .agent import Agent

# This allows the agent router to automatically discover and load the agent
Agent = Agent
