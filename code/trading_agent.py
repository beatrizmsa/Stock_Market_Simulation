from spade.behaviour import PeriodicBehaviour
from spade.agent import Agent
from spade.message import Message
import datetime


class StockTradingAgent(Agent):
    def __init__(self, agent_id, password, environment):
        super().__init__(agent_id, password)
        self.environment = environment
        if self.environment.day_interval == 1:
            environment.update_remaining_cash(agent_id, 10000)    # Set an initial balance of €10000
        self.indices = [33, 12, 7, 28, 27, 9, 1]                  # Stocks interested by the agent
        self.available_stocks = [self.environment.stocks[i] for i in self.indices]

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
            # Retrieve the initial day_interval value
            day_interval = self.agent.environment.get_day_interval()

            # For the interested stocks
            for stock in available_stocks:
                owned_quantity = self.agent.environment.get_stock_quantity(agent_name, stock)
                cash = self.agent.environment.get_remaining_cash(agent_name)
                # Maximum money that can be spent for each company
                if cash < 1000:
                    max_budget = cash
                else:
                    max_budget = 1000

                tickers_hist = self.agent.environment.get_stock_history(stock)
                stock_price = self.agent.environment.get_stock_value(stock)
                self.agent.environment.update_stock_max_value(agent_name, stock)

                # Check if it's possible to buy
                if self.should_buy(tickers_hist, day_interval):
                    action = "Buy"
                    quantity = int(max_budget / stock_price)
                    cost = quantity * stock_price

                    # Assesses if there is enough money for the purchase
                    if cost <= cash and quantity > 0:
                        self.agent.environment.update_stock_buying_value(agent_name, stock)
                        message = f"{action} {quantity} shares of {stock} for ${cost:.2f}"
                        await self.send_message_to_stockmarket(message)
                        print(f"{self.agent.name} sends: {message}")
                        message = await self.receive(timeout=5)
                        print(message.body + "\n")

                # If not, check if it's possible to sell
                elif owned_quantity > 0 and self.should_sell(tickers_hist, day_interval, agent_name, stock):
                    action = "Sell"
                    quantity = int(owned_quantity * 0.8 + 0.5)     # Selling 80% of the stocks of a company
                    revenue = quantity * stock_price
                    message = f"{action} {quantity} shares of {stock} for ${revenue:.2f}"
                    await self.send_message_to_stockmarket(message)
                    print(f"{self.agent.name} sends: {message}")
                    message = await self.receive(timeout=5)
                    print(message.body + "\n")

            print(f"{self.agent.name} owns {self.agent.environment.get_owned_stocks(str(agent_name))} shares and "
                  f"${self.agent.environment.get_remaining_cash(str(agent_name)):.2f} in cash")
            print(f"{self.agent.environment.get_total_value(str(agent_name))} is the total value of "
                  f"{self.agent.name}'s portfolio\n")

        def should_buy(self, stock_history, day_interval):
            current_price_open = stock_history["Open"].iloc[day_interval]
            price_anterior = stock_history["Open"].iloc[day_interval - 7]    # Price for 7 days ago
            price_yesterday = stock_history["Open"].iloc[day_interval - 1]   # Yesterday's price
            slope_seven = (current_price_open - price_anterior) / 7          # Calculates the slope over a seven-day interval
            slope_one = (current_price_open - price_yesterday)               # Calculates the slope with the previous day
            mean_slope = (slope_seven + slope_one) / 2                       # Find the average of the slopes
            return mean_slope > 1.2                                          # Sell if the average is greater than 1.2

        def should_sell(self, stock_history, day_interval, agent_id, stock):
            current_price = stock_history["Open"].iloc[day_interval]
            max_value = self.agent.environment.get_stock_max_value(agent_id, stock)
            buy_price = self.agent.environment.get_stock_buying_value(agent_id, stock)

            # Compares the purchase price of the share with the current price and also checks if the maximum recorded value of the share is more than 2% of the current price
            return buy_price / current_price > 1.02 or max_value / current_price > 1.02

    async def setup(self):
        start_at = datetime.datetime.now() + datetime.timedelta(seconds=5)
        self.add_behaviour(self.TradeBehaviour(period=75, start_at=start_at))
