from spade.behaviour import PeriodicBehaviour
from spade.agent import Agent
from spade.message import Message
import datetime


class BrokerAgent(Agent):
    def __init__(self, agent_id, password, environment):
        super().__init__(agent_id, password)
        self.environment = environment
        self.indices = [4, 0, 17, 28, 25, 9]            # Stocks interested by the agent
        self.available_stocks = [self.environment.stocks[i] for i in self.indices]
        if self.environment.day_interval == 1:
            environment.update_remaining_cash(agent_id, 3000)     # updates the agent's initial cash in the environment

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
            cash_stock = [cash*0.5, cash*0.3, cash*0.2]      # Distributes the available cash among different stocks (50%, 30%, and 20%)

            for stock in available_stocks:
                tickers_hist = self.agent.environment.get_stock_history(stock)
                self.agent.environment.update_stock_max_value(agent_name, stock)
                slope_thirty, prediction = self.calculate_prediction(tickers_hist, day_interval)
                stocks_value_buy[stock] = self.should_buy(prediction, slope_thirty)
                stocks_value_sell[stock] = self.should_sell(prediction, slope_thirty)

            sorted_stocks_buy = sorted(stocks_value_buy.items(), key=lambda x: x[1], reverse=True)
            top_three_positive_stocks = [(key, value) for key, value in sorted_stocks_buy if value != -2][:3]

            if len(top_three_positive_stocks) > 0:
                message = f"Buy"
                i = 0

                for stock, _ in top_three_positive_stocks:
                    stock_price = self.agent.environment.get_stock_value(stock) * 1.01    # 1% fees
                    quantity = int(cash_stock[i]/stock_price)
                    if quantity > 0:
                        self.agent.environment.update_stock_buying_value(agent_name, stock)
                        self.agent.environment.update_stock_buying_value("broker@localhost", stock)
                        message += f" {stock} : {quantity}"
                    i += 1

                if message != "Buy":
                    await self.send_message_to_broker(message)
                    print(f"{self.agent.name} sends: {message}")
                    message = await self.receive(timeout=10)
                    if message:
                        print(message.body + "\n")
            sorted_stocks_sell = sorted(stocks_value_sell.items(), key=lambda x: x[1], reverse=False)
            top_three_negative_stocks = [(key, value) for key, value in sorted_stocks_sell if self.agent.environment.get_stock_quantity(str(agent_name), key) > 0 and value != -2 and value < 0][:3]

            if len(top_three_negative_stocks) > 0:
                message = f"Sell"
                for stock, _ in top_three_negative_stocks:
                    message += f" {stock}"
                await self.send_message_to_broker(message)
                print(f"{self.agent.name} sends: {message}")
                message = await self.receive(timeout=10)
                print(message.body + "\n")

            print(f"{self.agent.name} owns {self.agent.environment.get_owned_stocks(str(agent_name))} shares and "
                  f"${self.agent.environment.get_remaining_cash(str(agent_name)):.2f} in cash")
            print(f"{total_value} is the total value of {self.agent.name}'s portfolio\n")

        # Method for calculating forecasts based on historical stock prices
        def calculate_prediction(self, stock_history, day_interval):
            current_price_open = stock_history["Open"].iloc[day_interval]
            price_yesterday = stock_history["Open"].iloc[day_interval - 1]     # the opening price from the previous day
            price_last_month = stock_history["Open"].iloc[day_interval - 31]   # the opening price from 31 days ago
            slope_thirty = (price_yesterday - price_last_month) / (30 * price_last_month)   # calculated as the percentage change between the price from the previous day and the price from 31 days ago
            prediction = (current_price_open - price_yesterday*(1 + slope_thirty)) / price_yesterday*(1 + slope_thirty)  # estimates the future price change using the current price, the price from the previous day, and the calculated slope
            return slope_thirty, prediction

        # assesses if the prediction exceeds the calculated slope and is a positive value
        def should_buy(self, prediction, slope_thirty):
            if prediction > slope_thirty and prediction > 0:
                return slope_thirty
            else:
                return -2

        # evaluates if the slope is negative
        def should_sell(self, prediction, slope_thirty):
            if slope_thirty < 0:
                return prediction
            else:
                return -2

    async def setup(self):
        start_at = datetime.datetime.now() + datetime.timedelta(seconds=20)
        self.add_behaviour(self.TradeBehaviour(period=75, start_at=start_at))
