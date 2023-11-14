from spade.behaviour import CyclicBehaviour
from spade.agent import Agent
from spade.message import Message


class BrokerAgent(Agent):
    def __init__(self, agent_id, password, environment):
        super().__init__(agent_id, password)
        self.environment = environment
        if self.environment.day_interval == 1:
            environment.update_remaining_cash(agent_id, 3000)
        self.indices = [33, 12, 7, 28, 27, 9, 1]
        self.available_stocks = [self.environment.stocks[i] for i in self.indices]

    class TradeBehaviour(CyclicBehaviour):
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
            stocks_value_buy = {}
            stocks_value_sell = {}
            for stock in available_stocks:
                tickers_hist = self.agent.environment.get_stock_history(stock)
                self.agent.environment.update_stock_max_value(agent_name, stock)
                stocks_value_buy[stock] = self.should_buy(tickers_hist, day_interval)
                # stocks_value_sell[stock] = self.should_sell(tickers_hist, day_interval, agent_name, stock)

            sorted_stocks_buy = sorted(stocks_value_buy.items(), key=lambda x: x[1], reverse=True)
            top_three_positive_stocks = [(key, value) for key, value in sorted_stocks_buy if value > 0][:3]
            if len(top_three_positive_stocks) > 0:
                message = f"Buy"
                for stock, _ in top_three_positive_stocks:
                    self.agent.environment.update_owned_stocks(agent_name, stock, 1)
                    message += f" {stock} "
                await self.send_message_to_broker(message)
                print(message)
            sorted_stocks_sell = sorted(stocks_value_buy.items(), key=lambda x: x[1], reverse=False)
            top_three_negative_stocks = [(key, value) for key, value in sorted_stocks_sell if self.agent.environment.get_stock_quantity(str(agent_name), key) > 0 and value < 0][:3]
            if len(top_three_negative_stocks) > 0:
                message = f"Sell"
                for stock, _ in top_three_negative_stocks:
                    message += f" {stock} "
                await self.send_message_to_broker(message)
                print(message)
            self.agent.environment.update_day_interval()
            print(f"{self.agent.name} owns {self.agent.environment.get_owned_stocks(str(agent_name))} shares and "
                  f"${self.agent.environment.get_remaining_cash(str(agent_name)):.2f} in cash")

        def should_buy(self, stock_history, day_interval):
            current_price_open = stock_history["Open"].iloc[day_interval]
            price_lastmonth = stock_history["Open"].iloc[day_interval - 30]
            price_lastweek = stock_history["Open"].iloc[day_interval - 7]
            slope_thirty = (current_price_open - price_lastmonth) / (30 * price_lastmonth)
            slope_seven = (current_price_open - price_lastweek) / (7 * price_lastweek)
            mean_slope = (slope_thirty*0.81 + slope_seven*0.19)
            print(f"the slopes are {slope_thirty} and {slope_seven}")
            return mean_slope

        def should_sell(self, stock_history, day_interval, agent_id, stock):
            current_price = stock_history["Open"].iloc[day_interval]
            # max_value = self.agent.environment.get_stock_max_value(agent_id, stock)
            buy_price = self.agent.environment.get_stock_buying_value(agent_id, stock)#ola biazinha
            return buy_price / current_price

    async def setup(self):
        self.add_behaviour(self.TradeBehaviour())

