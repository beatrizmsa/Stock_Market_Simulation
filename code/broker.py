from spade.behaviour import CyclicBehaviour
from spade.agent import Agent
from spade.message import Message


class Broker(Agent):
    def __init__(self, agent_id, password, environment):
        super().__init__(agent_id, password)
        self.environment = environment
        self.tax = 0.01                                           # 1% flat fee for broker transactions
        self.available_stocks = ["GOOGL", "AAPL", "AMZN"]         # Stocks interested by the broker
        if self.environment.day_interval == 1:
            environment.update_remaining_cash(agent_id, 120000)   # Set the initial balance of the broker
            value = 8
            for stock in self.available_stocks:
                self.environment.update_owned_stocks("broker@localhost", stock, value)
                self.environment.update_stock_buying_value(agent_id, stock)
                value /= 2

    class BrokerInteraction(CyclicBehaviour):
        async def send_message_to_agent(self, message_content, agent_id):
            # Create a new message
            message = Message(to=str(agent_id))
            message.body = message_content

            # Send the message
            await self.send(message)

        async def send_message_to_stockmarket(self, message_content):
            # Create a new message
            message = Message(to="stockmarket@localhost")
            message.body = message_content

            # Send the message
            await self.send(message)

        # Method of selling shares to a specific agent
        def sell_to_client(self, agent_id, stock, cost, quantity):
            tax = self.agent.tax * cost     # Calculates tax based on total cost
            self.agent.environment.update_owned_stocks(agent_id, stock, quantity)
            self.agent.environment.update_remaining_cash(agent_id, -(cost + tax))
            self.agent.environment.update_owned_stocks("broker@localhost", stock, -quantity)
            self.agent.environment.update_remaining_cash("broker@localhost", cost + tax)

        # Method of purchasing shares for a specific agent
        def buy_from_client(self, agent_id, stock, cost, quantity):
            tax = self.agent.tax * cost     # # Calculates tax based on total cost
            self.agent.environment.update_owned_stocks(agent_id, stock, -quantity)
            self.agent.environment.update_remaining_cash(agent_id, cost - tax)
            self.agent.environment.update_owned_stocks("broker@localhost", stock, quantity)
            self.agent.environment.update_remaining_cash("broker@localhost", -(cost - tax))

        async def run(self):
            message = await self.receive(timeout=5)
            if message:
                message_content = message.body
                sender = str(message.sender)
                if message_content.startswith("Buy"):
                    action = "Buy"
                    message_words = message_content.split(" ")
                    num_stocks = int((len(message_words)-1) / 3)
                    for i in range(num_stocks):
                        stock, _, quantity = message_words[(i*3)+1: i*3 + 4]  # Breaks down the message to determine which stocks to buy
                        quantity = int(quantity)
                        cost = quantity * self.agent.environment.get_stock_value(stock)
                        message = f"{action} {quantity} shares of {stock} for ${cost:.2f}"
                        await self.send_message_to_stockmarket(message)
                        await self.receive(timeout=5)
                        self.sell_to_client(sender, stock, cost, quantity)
                    await self.send_message_to_agent("Transaction complete", sender)

                elif message_content.startswith("Sell"):
                    action = "Sell"
                    message_words = message_content.split(" ")
                    num_stocks = int(len(message_words)-1)  # Breaks down the message to determine which stocks to buy
                    for i in range(num_stocks):
                        stock = message_words[i+1]
                        quantity = self.agent.environment.get_stock_quantity(sender, stock)
                        cost = self.agent.environment.get_stock_value(stock) * quantity
                        self.buy_from_client(sender, stock, cost, quantity)
                        message = f"{action} {quantity} shares of {stock} for ${cost:.2f}"
                        await self.send_message_to_stockmarket(message)
                        await self.receive(timeout=5)
                    await self.send_message_to_agent("Transaction complete", sender)

    async def setup(self):
        self.add_behaviour(self.BrokerInteraction())
