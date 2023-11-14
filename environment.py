import yfinance as yf
import json
from datetime import datetime, timedelta
from spade.behaviour import CyclicBehaviour
from spade.agent import Agent
from spade.message import Message


class Environment:
    def __init__(self):
        self.owned_stocks = {}
        self.remaining_cash = {}
        self.stock_max_value = {}
        self.stock_buying_value = {}
        self.max_buying_quantity = {}
        self.time_end = datetime.now()-timedelta(hours=25)
        self.time_start = self.time_end - timedelta(days=1000)
        self.day_interval = 1
        with open('stocks.txt', 'r') as file:
            self.stocks = [line.strip() for line in file.readlines()]

    def save_to_file(self):
        data = {
            'owned_stocks': self.owned_stocks,
            'remaining_cash': self.remaining_cash,
            'stock_max_value': self.stock_max_value,
            'stock_buying_value': self.stock_buying_value,
            'max_buying_quantity': self.max_buying_quantity,
            'time_end': self.time_end.isoformat(),
            'time_start': self.time_start.isoformat(),
            'day_interval': self.day_interval
        }

        with open('dados.txt', 'w') as file:
            json.dump(data, file)

    def load_from_file(self):
        try:
            with open('dados.txt', 'r') as file:
                data = json.load(file)

            self.owned_stocks = data.get('owned_stocks', {})
            self.remaining_cash = data.get('remaining_cash', {})
            self.stock_max_value = data.get('stock_max_value', {})
            self.stock_buying_value = data.get('stock_buying_value', {})
            self.max_buying_quantity = data.get('max_buying_quantity', {})
            self.time_end = datetime.fromisoformat(data.get('time_end', ''))
            self.time_start = datetime.fromisoformat(data.get('time_start', ''))
            self.day_interval = data.get('day_interval', 1)

        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            self.__init__()
        print(f"Day {self.day_interval}")

    def update_owned_stocks(self, agent_id, stock, quantity):
        if agent_id not in self.owned_stocks:
            self.owned_stocks[agent_id] = {}
        if stock not in self.owned_stocks[agent_id]:
            self.owned_stocks[agent_id][stock] = 0
        self.owned_stocks[agent_id][stock] += quantity

    def update_remaining_cash(self, agent_id, quantity):
        if agent_id not in self.remaining_cash:
            self.remaining_cash[agent_id] = 0
        self.remaining_cash[agent_id] += quantity

    def update_stock_max_value(self, agent_id, stock):
        value = self.get_stock_value(stock)
        if agent_id not in self.stock_max_value:
            self.stock_max_value[agent_id] = {}
        if stock not in self.stock_max_value[agent_id]:
            self.stock_max_value[agent_id][stock] = value
        elif self.stock_max_value[agent_id][stock] < value:
            self.stock_max_value[agent_id][stock] = value

    def update_stock_buying_value(self, agent_id, stock):
        value = self.get_stock_value(stock)
        if agent_id not in self.stock_buying_value:
            self.stock_buying_value[agent_id] = {}
        if stock not in self.stock_buying_value[agent_id]:
            self.stock_buying_value[agent_id][stock] = value
        elif self.stock_buying_value[agent_id][stock] < value:
            self.stock_buying_value[agent_id][stock] = value

    def update_day_interval(self):
        self.day_interval += 1
        self.save_to_file()
        print(f"Day {self.day_interval}")

    def get_owned_stocks(self, agent_id):
        # print(self.owned_stocks)
        return self.owned_stocks.get(agent_id, {})

    def get_stock_quantity(self, agent_id, stock):
        owned_stocks = self.get_owned_stocks(agent_id)
        return owned_stocks.get(stock, 0)

    def get_remaining_cash(self, agent_id):
        return self.remaining_cash.get(agent_id, 0)

    def get_day_interval(self):
        return self.day_interval

    def get_stock_value(self, stock):
        stock_data = yf.Ticker(stock)
        interval = '1d'
        tickers_hist = stock_data.history(start=self.time_start, end=self.time_end, interval=interval)
        # tickers_hist['Open'].to_csv('dados.txt', sep='\t', index=False)
        return tickers_hist["Open"].iloc[self.day_interval]

    def get_stock_history(self, stock):
        stock_data = yf.Ticker(stock)
        return stock_data.history(start=self.time_start, end=self.time_end, interval='1d')

    def get_portfolio_value(self, agent_id):
        total = 0
        owned_stocks = self.get_owned_stocks(agent_id)
        for stock, quantity in owned_stocks.items():
            value = self.get_stock_value(stock)
            total += value * quantity
        return total

    def get_total_value(self, agent_id):
        total = 0
        owned_stocks = self.get_owned_stocks(agent_id)
        for stock, quantity in owned_stocks.items():
            value = self.get_stock_value(stock)
            total += value * quantity
        cash = self.get_remaining_cash(agent_id)
        return total + cash

    def get_stock_max_value(self, agent_id, stock):
        return self.stock_max_value[agent_id][stock]

    def get_stock_buying_value(self, agent_id, stock):
        return self.stock_buying_value[agent_id][stock]

class StockMarketAgent(Agent):
    def __init__(self, agent_id, password, environment):
        super().__init__(agent_id, password)
        self.environment = environment

    class StockMarketInteraction(CyclicBehaviour):
        async def send_message_to_agent(self, message_content, agent_id):
            # Create a new message
            message = Message(to=str(agent_id))
            message.body = message_content

            # Send the message
            await self.send(message)

        async def run(self):
            message = await self.receive(timeout=5)
            # print(message)
            if message:
                # Process the received message
                message_content = message.body
                sender = message.sender
                # print(self.agent.environment.get_owned_stocks(sender))
                print(f"{self.agent.name} received: {message_content} from {sender}")
                if message_content.startswith("Buy"):
                    action, quantity, _, _, stock, _, cost = message_content.split(" ")
                    cost = cost.strip("$")
                    self.agent.environment.update_remaining_cash(str(sender), -float(cost))
                    self.agent.environment.update_owned_stocks(str(sender), stock, int(quantity))
                    await self.send_message_to_agent("Transaction complete", sender)
                    # print(f"{sender} buys {quantity} shares of {stock} for ${cost}")
                else:
                    action, quantity, _, _, stock, _, revenue = message_content.split(" ")
                    revenue = revenue.strip("$")
                    self.agent.environment.update_remaining_cash(str(sender), float(revenue))
                    self.agent.environment.update_owned_stocks(str(sender), stock, -int(quantity))
                    await self.send_message_to_agent("Transaction complete", sender)
                    # print(f"{sender} sells {quantity} shares of {stock} for ${revenue}")

    async def setup(self):
        self.add_behaviour(self.StockMarketInteraction())
