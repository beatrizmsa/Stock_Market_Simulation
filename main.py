import asyncio
from environment import Environment, StockMarketAgent
from trading_agent import StockTradingAgent
from broker_agent import BrokerAgent
from spade import wait_until_finished


async def main():
    env = Environment()
    stockmarket_agent = StockMarketAgent("stockmarket@localhost", "", env)
    # stockmarket_agent.add_behaviour(StockMarketAgent.StockMarketInteraction())
    await stockmarket_agent.start()
    env.load_from_file()
    trading_agent = BrokerAgent("admin@localhost", "12345678", env)
    # await trading_agent.setup()
    await trading_agent.start()
    await wait_until_finished(stockmarket_agent)
    await wait_until_finished(trading_agent)

if __name__ == "__main__":
    asyncio.run(main())
