from spade.behaviour import PeriodicBehaviour
from spade.agent import Agent
from spade.message import Message
import datetime


class BrokerAgent2(Agent):
    def __init__(self, agent_id, password, environment):
        super().__init__(agent_id, password)
        self.environment = environment
        if self.environment.day_interval == 1:
            environment.update_remaining_cash(agent_id, 4500)      # updates the agent's initial cash in the environment
        self.indices = [3, 4, 7]             # Stocks interested by the agent
        self.available_stocks = [self.environment.stocks[i] for i in self.indices]

    class TradeBehaviour(PeriodicBehaviour):
        async def send_message_to_broker(self, message_content):
            # Create a new message
            message = Message(to="broker@localhost")
            message.body = message_content

            # Send the message
            await self.send(message)

        async def run(self):
            available_stocks = self.agent.available_stocks
            agent_name = f"{self.agent.name}@localhost"
            day_interval = self.agent.environment.get_day_interval()
            total_value = self.agent.environment.get_total_value(str(agent_name))
            stocks_value_buy = {}
            stocks_value_sell = {}
            cash = self.agent.environment.get_remaining_cash(agent_name)

            for stock in available_stocks:
                tickers_hist = self.agent.environment.get_stock_history(stock)
                self.agent.environment.update_stock_max_value(agent_name, stock)
                sum = self.heuristic(tickers_hist, day_interval)
                stocks_value_buy[stock] = self.should_buy(sum)
                stocks_value_sell[stock] = self.should_sell(sum)

            sorted_stocks_buy = sorted(stocks_value_buy.items(), key=lambda x: x[1], reverse=True)
            top_three_positive_stocks = [(key, value) for key, value in sorted_stocks_buy if value != 0][:3]

            if len(top_three_positive_stocks) > 0:
                message = f"Buy"
                i = 0

                for stock, _ in top_three_positive_stocks:
                    stock_price = self.agent.environment.get_stock_value(stock) * 1.01      # 1% fees
                    quantity = int(cash/stock_price)
                    cash -= quantity*stock_price
                    if quantity > 0:
                        self.agent.environment.update_stock_buying_value(agent_name, stock)
                        self.agent.environment.update_stock_buying_value("broker@localhost", stock)
                        message += f" {stock} : {quantity}"
                    i += 1

                if message != "Buy":
                    await self.send_message_to_broker(message)
                    print(f"{self.agent.name} sends: {message}")
                    message = await self.receive(timeout=5)
                    print(message.body + "\n")
            sorted_stocks_sell = sorted(stocks_value_sell.items(), key=lambda x: x[1], reverse=False)
            top_three_negative_stocks = [(key, value) for key, value in sorted_stocks_sell if self.agent.environment.get_stock_quantity(str(agent_name), key) > 0 and value != 0][:3]

            if len(top_three_negative_stocks) > 0:
                message = f"Sell"
                for stock, _ in top_three_negative_stocks:
                    message += f" {stock}"
                await self.send_message_to_broker(message)
                print(f"{self.agent.name} sends: {message}")
                message = await self.receive(timeout=5)
                print(message.body + "\n")

            print(f"{self.agent.name} owns {self.agent.environment.get_owned_stocks(str(agent_name))} shares and "
                  f"${self.agent.environment.get_remaining_cash(str(agent_name)):.2f} in cash")
            print(f"{total_value} is the total value of {self.agent.name}'s portfolio\n")

        # This function calculates a heuristic value by iterating over a seven days
        def heuristic(self, stock_history, day_interval):
            soma = 0
            for i in range(7):
                price = stock_history["Open"].iloc[day_interval - i]
                price_anterior = stock_history["Open"].iloc[day_interval - i - 1]
                soma += price-price_anterior  # the difference between the opening price of the current day and the previous day's opening price
            return soma

        def should_buy(self, value):
            if value > 0:
                return value
            else:
                return 0

        def should_sell(self, value):
            if value < 0:
                return value
            else:
                return 0

    async def setup(self):
        start_at = datetime.datetime.now() + datetime.timedelta(seconds=35)
        self.add_behaviour(self.TradeBehaviour(period=75, start_at=start_at))
