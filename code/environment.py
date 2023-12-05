import yfinance as yf
import numpy as np
import json
import socket
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
        self.stock_selling_value = {}
        self.max_buying_quantity = {}
        self.time_end = datetime.now()-timedelta(hours=25)
        self.time_start = self.time_end - timedelta(days=1000)
        self.day_interval = 1
        with open('stocks.txt', 'r') as file:
            self.stocks = [line.strip() for line in file.readlines()]

    # Save the environment information to a JSON file
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

    # Load the information from the JSON file to initialize the environment
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

        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            self.__init__()
        print(f"----- Day {self.day_interval} -----")

    # Update the quantity of stocks that an agent possesses
    def update_owned_stocks(self, agent_id, stock, quantity):
        if agent_id not in self.owned_stocks:
            self.owned_stocks[agent_id] = {}
        if stock not in self.owned_stocks[agent_id]:
            self.owned_stocks[agent_id][stock] = 0
        self.owned_stocks[agent_id][stock] += quantity

    # Update the amount of money that an agent has
    def update_remaining_cash(self, agent_id, quantity):
        if agent_id not in self.remaining_cash:
            self.remaining_cash[agent_id] = 0
        self.remaining_cash[agent_id] += quantity

    # Update the maximum buying value of the stocks
    def update_stock_max_value(self, agent_id, stock):
        value = self.get_stock_value(stock)
        if agent_id not in self.stock_max_value:
            self.stock_max_value[agent_id] = {}
        if stock not in self.stock_max_value[agent_id]:
            self.stock_max_value[agent_id][stock] = value
        elif self.stock_max_value[agent_id][stock] < value:
            self.stock_max_value[agent_id][stock] = value

    # Update the buying value of stocks for an agent
    def update_stock_buying_value(self, agent_id, stock):
        value = self.get_stock_value(stock)
        if agent_id not in self.stock_buying_value:
            self.stock_buying_value[agent_id] = {}
        if stock not in self.stock_buying_value[agent_id]:
            self.stock_buying_value[agent_id][stock] = value
        elif self.stock_buying_value[agent_id][stock] < value:
            self.stock_buying_value[agent_id][stock] = value

    # Update the day interval in the environment and update the data file
    def update_day_interval(self):
        self.day_interval += 1
        self.save_to_file()
        print(f"----- Day {self.day_interval} -----")

    # Returns a dictionary with the stocks owned by a specific agent
    def get_owned_stocks(self, agent_id):
        # print(self.owned_stocks)
        return self.owned_stocks.get(agent_id, {})

    # Returns the quantity of a specific type of stock that an agent owns
    def get_stock_quantity(self, agent_id, stock):
        owned_stocks = self.get_owned_stocks(agent_id)
        return owned_stocks.get(stock, 0)

    # Returns the remaining amount of money for an agent
    def get_remaining_cash(self, agent_id):
        return round(self.remaining_cash.get(agent_id, 0), 2)

    # Returns the current day interval
    def get_day_interval(self):
        return self.day_interval

    # Gets the current value of a specific stock
    def get_stock_value(self, stock):
        stock_data = yf.Ticker(stock)
        interval = '1d'
        tickers_hist = stock_data.history(start=self.time_start, end=self.time_end, interval=interval)
        return tickers_hist["Open"].iloc[self.day_interval]

    # Returns the history of a stock
    def get_stock_history(self, stock):
        stock_data = yf.Ticker(stock)
        return stock_data.history(start=self.time_start, end=self.time_end, interval='1d')

    # Calculates the total value of an agent's portfolio
    def get_portfolio_value(self, agent_id):
        total = 0
        owned_stocks = self.get_owned_stocks(agent_id)
        for stock, quantity in owned_stocks.items():
            value = self.get_stock_value(stock)
            total += value * quantity
        return round(total, 2)

    # Calculates the total value of the agent, including the portfolio and cash
    def get_total_value(self, agent_id):
        total = 0
        owned_stocks = self.get_owned_stocks(agent_id)
        for stock, quantity in owned_stocks.items():
            value = self.get_stock_value(stock)
            total += value * quantity
        cash = self.get_remaining_cash(agent_id)
        return round(total + cash, 2)

    # Returns the maximum value of a stock for an agent
    def get_stock_max_value(self, agent_id, stock):
        return self.stock_max_value[agent_id][stock]

    # Returns the buying value of a stock for an agent
    def get_stock_buying_value(self, agent_id, stock):
        return self.stock_buying_value[agent_id][stock]

    # Returns the selling value of a stock for an agent
    def get_stock_selling_value(self, agent_id, stock):
        if agent_id not in self.stock_selling_value:
            self.stock_selling_value[agent_id] = {}
        if stock not in self.stock_selling_value[agent_id]:
            self.stock_selling_value[agent_id][stock] = 0
        return self.stock_selling_value[agent_id][stock]

    # allows you to get the opening prices of a specific stock within a given date range
    def get_stock_days(self, stock, start_day, end_day):
        stock_data = yf.Ticker(stock)
        interval = '1d'
        tickers_hist = stock_data.history(start=start_day, end=end_day, interval=interval)
        return np.array(tickers_hist["Open"])


# The agent responsible for the interaction between agents and the environment
class StockMarketAgent(Agent):
    def __init__(self, agent_id, password, environment):
        super().__init__(agent_id, password)
        self.environment = environment

    class StockMarketInteraction(CyclicBehaviour):
        async def send_message_to_interface(self, message_content):
            host = '127.0.0.1'
            port = 12345

            try:
                # Connect to interface server
                interface_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                interface_socket.connect((host, port))

                # Send the message
                interface_socket.send(message_content.encode('utf-8'))

                # Close the connection
                interface_socket.close()

            except ConnectionRefusedError:
                print("Error: Could not connect to the interface server.")

        async def send_message_to_agent(self, message_content, agent_id):
            # Create a new message
            message = Message(to=str(agent_id))
            message.body = message_content

            # Send the message
            await self.send(message)

        async def run(self):
            message = await self.receive(timeout=5)
            if message:
                # Process the received message
                message_content = message.body
                sender = message.sender
                print(f"{self.agent.name} received: {message_content} from {sender}")
                if message_content.startswith("Buy"):
                    action, quantity, _, _, stock, _, cost = message_content.split(" ")
                    cost = cost.strip("$")
                    self.agent.environment.update_remaining_cash(str(sender), -float(cost))
                    self.agent.environment.update_owned_stocks(str(sender), stock, int(quantity))
                    await self.send_message_to_interface(f"{message_content} from {sender}")
                    await self.send_message_to_agent("Transaction complete", sender)
                elif message_content.startswith("Sell"):
                    action, quantity, _, _, stock, _, revenue = message_content.split(" ")
                    revenue = revenue.strip("$")
                    self.agent.environment.update_remaining_cash(str(sender), float(revenue))
                    self.agent.environment.update_owned_stocks(str(sender), stock, -int(quantity))
                    await self.send_message_to_interface(f"{message_content} from {sender}")
                    await self.send_message_to_agent("Transaction complete", sender)
                else:
                    await self.send_message_to_interface(f"Received: {message_content}")

    async def setup(self):
        self.add_behaviour(self.StockMarketInteraction())
