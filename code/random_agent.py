import datetime
from spade.behaviour import PeriodicBehaviour
from spade.agent import Agent
from spade.message import Message
import random


class RandomAgent(Agent):
    def __init__(self, agent_id, password, environment):
        super().__init__(agent_id, password)
        self.environment = environment
        if self.environment.day_interval == 1:
            environment.update_remaining_cash(agent_id, 2000)   # Set an initial balance of €2000
        self.indices = [15, 2, 17, 29, 14]                      # Stocks interested by the agent
        self.available_stocks = [self.environment.stocks[i] for i in self.indices]

        # Initial decision thresholds
        self.buy_threshold = 0.7        # Initial buy decision threshold
        self.sell_threshold = 0.3       # Initial sell decision threshold
        self.max_adjust_attempts = 5    # Maximum number of adjustment attempts
        self.consecutive_attempts = 0   # Attempts counter

    class TradeBehaviour(PeriodicBehaviour):
        async def send_message_to_stockmarket(self, message_content):
            # Create a new message
            message = Message(to="stockmarket@localhost")
            message.body = message_content

            # Send the message
            await self.send(message)

        async def run(self):
            available_stocks = self.agent.available_stocks
            agent_name = f"{self.agent.name}@localhost"
            total_value = self.agent.environment.get_total_value(str(agent_name))

            # For the interested stocks
            for stock in available_stocks:
                owned_quantity = self.agent.environment.get_stock_quantity(agent_name, stock)
                cash = self.agent.environment.get_remaining_cash(agent_name)

                stock_price = self.agent.environment.get_stock_value(stock)
                self.agent.environment.update_stock_max_value(agent_name, stock)
                prediction = random.randint(0, 1)          # Random prediction about the stock movement
                media_influence = random.randint(-1, 1)      # Random value for media influence
                media_weight = 0.2                             # Weight of media influence
                decision = prediction + media_influence * media_weight

                # Adjust decision thresholds based on total worth
                self.agent.adjust_decision_thresholds(total_value)

                # Evaluates whether to buy
                if self.should_buy(decision):
                    action = "Buy"
                    quantity = random.randint(1, 6)     # Random quantity of shares of a company
                    cost = quantity * stock_price

                    # Assesses if there is enough money for the purchase
                    if cost <= cash:
                        self.agent.environment.update_stock_buying_value(agent_name, stock)
                        message = f"{action} {quantity} shares of {stock} for ${cost:.2f}"
                        await self.send_message_to_stockmarket(message)
                        print(f"{self.agent.name} sends: {message}")
                        message = await self.receive(timeout=5)
                        print(message.body + "\n")

                # Assesses if there are stocks and whether to sell
                elif owned_quantity > 0 and self.should_sell(decision):
                    action = "Sell"
                    quantity = random.randint(1, owned_quantity)
                    revenue = stock_price * quantity
                    message = f"{action} {quantity} shares of {stock} for ${revenue:.2f}"
                    await self.send_message_to_stockmarket(message)
                    print(f"{self.agent.name} sends: {message}")
                    message = await self.receive(timeout=5)
                    print(message.body + "\n")

            print(f"{self.agent.name} owns {self.agent.environment.get_owned_stocks(str(agent_name))} shares and "
                  f"${self.agent.environment.get_remaining_cash(str(agent_name)):.2f} in cash")
            print(f"{total_value} is the total value of {self.agent.name}'s portfolio\n")

        def should_buy(self, decision):
            return decision > self.agent.buy_threshold

        def should_sell(self, decision):
            return decision < self.agent.sell_threshold

    # Adjusts the decision thresholds based on the total value of the agent's portfolio
    def adjust_decision_thresholds(self, total_value):
        # If total value is below a threshold, adjust randomly every 5 consecutive attempts until the value increases
        if total_value < 1900:
            self.consecutive_attempts += 1
            # If it reaches the maximum limit
            if self.consecutive_attempts == self.max_adjust_attempts:
                # Increase or decrease randomly by up to 0.1
                self.buy_threshold += random.uniform(-0.1, 0.1)
                self.sell_threshold += random.uniform(-0.1, 0.1)
                self.consecutive_attempts = 0
        # If it is greater than or equal to 1900, reset the attempts counter
        elif total_value >= 1900:
            self.consecutive_attempts = 0
        # If it's greater than 2500, set new fixed buy and sell thresholds to 0.6 and 0.4, respectively
        if total_value > 2500:
            self.buy_threshold = 0.6
            self.sell_threshold = 0.4

    async def setup(self):
        start_at = datetime.datetime.now() + datetime.timedelta(seconds=50)
        self.add_behaviour(self.TradeBehaviour(period=75, start_at=start_at))
