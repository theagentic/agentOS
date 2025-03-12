"""
SpotiAuto Agent Package

Handles Spotify automation for music playback and playlist management.
"""

# Temporarily use the template agent as a placeholder
from ..agent_template.agent import TemplateAgent

class SpotiAutoAgent(TemplateAgent):
    def __init__(self, config=None):
        super().__init__(config)
        self.agent_name = "spotiauto"

Agent = SpotiAutoAgent
