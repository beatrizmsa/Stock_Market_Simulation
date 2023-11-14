from spade.behaviour import CyclicBehaviour
from spade.agent import Agent
from spade.message import Message

class Broker(Agent):
    def __init__(self, agent_id, password, environment):
        super().__init__(agent_id, password)
        self.environment = environment
        environment.update_remaining_cash(agent_id, 120000)

    class BrokerInteraction(CyclicBehaviour):
        async def send_message_to_agent(self, message_content, agent_id):
            # Create a new message
            message = Message(to=str(agent_id))
            message.body = message_content

            # Send the message
            await self.send(message)

        async def process_order(self, message_content):
            # Create a new message
            message = Message(to="stockmarket@localhost")
            message.body = message_content

            # Send the message
            await self.send(message)

        async def run(self):
            message = await self.receive(timeout=5)
            if message:
                message_content = message.body
                if message_content.startswith("Buy"):
                    print("entrou")


    async def setup(self):
        self.add_behaviour(self.BrokerInteraction())