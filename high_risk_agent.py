from spade.behaviour import PeriodicBehaviour
from spade.agent import Agent
from spade.message import Message
import datetime


class HighRiskAgent(Agent):
    def __init__(self, agent_id, password, environment):
        super().__init__(agent_id, password)
        self.environment = environment
        if self.environment.day_interval == 1:
            environment.update_remaining_cash(agent_id, 5000)   # Set an initial balance of €5000
        self.indices = [37, 38, 39, 40, 42]                     # Stocks interested by the agent
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
            day_interval = self.agent.environment.get_day_interval()

            # Check the stocks interested by the agent
            for stock in available_stocks:
                owned_quantity = self.agent.environment.get_stock_quantity(agent_name, stock)
                cash = self.agent.environment.get_remaining_cash(agent_name)

                # Maximum money that can be spent for each company
                if cash < 1500:
                    max_budget = cash
                else:
                    max_budget = 1500

                tickers_hist = self.agent.environment.get_stock_history(stock)
                stock_price = self.agent.environment.get_stock_value(stock)
                self.agent.environment.update_stock_max_value(agent_name, stock)

                # Check if it's possible to buy
                if self.should_buy(tickers_hist, day_interval, agent_name, stock):
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
                    quantity = int(owned_quantity)        # Selling all stocks of a company
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

            # Update day_interval at the end of the loop
            self.agent.environment.update_day_interval()
            if self.agent.environment.day_interval % 7 == 0:
                await self.send_message_to_stockmarket("The week has ended")

        def should_sell(self, stock_history, day_interval, agent_id, stock):
            current_price = stock_history["Open"].iloc[day_interval]
            buy_price = self.agent.environment.get_stock_buying_value(agent_id, stock)

            # Calculate the percentage variation
            percent_change = ((current_price - buy_price) / buy_price) * 100

            # Sell if there is a profit of 25% or a loss of 8%
            if percent_change >= 25 or percent_change <= -8:
                return 1

            return 0

        def should_buy(self, stock_history, day_interval, agent_id, stock):
            s = self.agent.environment.get_stock_quantity(agent_id, stock)
            # Only buy when there are no stocks of that company
            if s == 0:
                current_price = stock_history["Open"].iloc[day_interval]
                sell_price = self.agent.environment.get_stock_selling_value(agent_id, stock)

                # If the selling price is equal to 0, it never bought any shares of that company
                if sell_price == 0:

                    # Check if there has been an increase in the last 3 days
                    flag = True
                    for i in range(1, 4):
                        if stock_history['Open'].iloc[day_interval - (i - 1)] < stock_history['Open'].iloc[day_interval - i]:
                            flag = False
                            break

                    if flag:
                        return True

                    return False

                else:
                    # Check if the current price is 5% below the selling value
                    if current_price <= (sell_price * 0.95):
                        # Check if there has been an increase in the last 3 days
                        flag = True
                        for i in range(1, 4):
                            if stock_history['Open'].iloc[day_interval - (i - 1)] < stock_history['Open'].iloc[day_interval - i]:
                                flag = False
                                break

                        if flag:
                            return True

                    return False
            return False

    async def setup(self):
        start_at = datetime.datetime.now() + datetime.timedelta(seconds=65)
        self.add_behaviour(self.TradeBehaviour(period=75, start_at=start_at))
