from core.agent_base import AgentBase

class SpotiautoAgent(AgentBase):
    def __init__(self):
        super().__init__()
        self.agent_id = "spotiauto"
    
    def process(self, command: str):
        return {
            "status": "info",
            "message": "This agent is not yet implemented.",
            "spoke": "This agent is not yet implemented."
        }
