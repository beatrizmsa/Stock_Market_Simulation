from spade.behaviour import CyclicBehaviour
from spade.agent import Agent
from spade.message import Message


class StockTradingAgent(Agent):
    def __init__(self, agent_id, password, environment):
        super().__init__(agent_id, password)
        self.environment = environment
        if self.environment.day_interval == 1:
            environment.update_remaining_cash(agent_id, 10000)
        self.indices = [33, 12, 7, 28, 27, 9, 1]
        self.available_stocks = [self.environment.stocks[i] for i in self.indices]

    class TradeBehaviour(CyclicBehaviour):
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
            # print(f"{self.agent.name} is in day {day_interval}")
            for stock in available_stocks:
                # max_quantity = random.randint(1, 20)
                # print(stock)
                # print(day_interval)
                owned_quantity = self.agent.environment.get_stock_quantity(agent_name, stock)
                cash = self.agent.environment.get_remaining_cash(agent_name)
                if cash < 1000:
                    max_budget = cash
                else:
                    max_budget = 1000

                # stock_data = yf.Ticker(stock)
                # end_date1 = self.agent.environment.time_end
                # start_date1 = self.agent.environment.time_start
                # tickers_hist = stock_data.history(start=start_date1, end=end_date1, interval='1d')
                # stock_price = tickers_hist["Open"].iloc[day_interval]
                tickers_hist = self.agent.environment.get_stock_history(stock)
                stock_price = self.agent.environment.get_stock_value(stock)
                self.agent.environment.update_stock_max_value(agent_name, stock)

                if self.should_buy(tickers_hist, day_interval):
                    action = "Buy"
                    quantity = int(max_budget / stock_price)
                    cost = quantity * stock_price

                    # print(max_budget)
                    # print(stock_price)
                    # print(quantity)
                    if cost <= cash and quantity > 0:
                        self.agent.environment.update_stock_buying_value(agent_name, stock)
                        # self.agent.environment.update_remaining_cash(agent_name, -cost)
                        # self.agent.environment.update_owned_stocks(agent_name, stock, quantity)
                        message = f"{action} {quantity} shares of {stock} for ${cost:.2f}"
                        await self.send_message_to_stockmarket(message)
                        print(f"{self.agent.name} sends: {message}")
                        message = await self.receive(timeout=15)
                        print(message.body + "\n")
                    else:
                        pass
                        # print(f"{self.agent.name} does not have enough money to buy more shares of {stock}\n")
                elif owned_quantity > 0 and self.should_sell(tickers_hist, day_interval, agent_name, stock):
                    action = "Sell"
                    quantity = int(owned_quantity * 0.8 + 0.5)
                    revenue = quantity * stock_price
                    # self.agent.environment.update_remaining_cash(agent_name, revenue)
                    # self.agent.environment.update_owned_stocks(agent_name, stock, -quantity)
                    message = f"{action} {quantity} shares of {stock} for ${revenue:.2f}"
                    await self.send_message_to_stockmarket(message)
                    print(f"{self.agent.name} sends: {message}")
                    message = await self.receive(timeout=15)
                    print(message.body + "\n")
                else:
                    #print(f"{self.agent.name} does not buy more {stock} (strategy decision)\n")
                    pass
            print(f"{self.agent.name} owns {self.agent.environment.get_owned_stocks(str(agent_name))} shares and "
                    f"${self.agent.environment.get_remaining_cash(str(agent_name)):.2f} in cash")
            print(f"{self.agent.environment.get_total_value(str(agent_name))} is the total value of {self.agent.name}'s portfolio\n")
            # Update day_interval at the end of the loop
            self.agent.environment.update_day_interval()

        def should_buy(self, stock_history, day_interval):
            current_price_open = stock_history["Open"].iloc[day_interval]
            price_anterior = stock_history["Open"].iloc[day_interval - 7]
            price_yesterday = stock_history["Open"].iloc[day_interval - 1]
            slope_seven = (current_price_open - price_anterior) / 7
            slope_one = (current_price_open - price_yesterday)
            mean_slope = (slope_seven + slope_one) / 2
            # print(mean_slope)
            return mean_slope > 1.2

        def should_sell(self, stock_history, day_interval, agent_id, stock):
            current_price = stock_history["Open"].iloc[day_interval]
            max_value = self.agent.environment.get_stock_max_value(agent_id, stock)
            buy_price = self.agent.environment.get_stock_buying_value(agent_id, stock)
            # print(f"maximo valor :{max_value}")
            # print(f"preco a que comprou: {buy_price}")
            # print(f"preco atual :{current_price}")
            # print(f"buy/current: {buy_price/current_price}")
            # print(f"max/curent: {max_value/current_price}")
            return buy_price / current_price > 1.02 or max_value / current_price > 1.02
            # current_price_open = stock_history["Open"].iloc[day_interval]
            # price_anterior = stock_history["Open"].iloc[day_interval - 1]0
            # print(current_price_open)
            # print(price_anterior)
            # return current_price_open < price_anterior * 1.04

    async def setup(self):
        self.add_behaviour(self.TradeBehaviour())


