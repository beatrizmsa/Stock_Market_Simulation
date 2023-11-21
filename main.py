import asyncio
from environment import Environment, StockMarketAgent
from trading_agent import StockTradingAgent
from broker_agent import BrokerAgent
from broker_agent2 import BrokerAgent2
from broker import Broker
from random_agent import RandomAgent
from high_risk_agent import HighRiskAgent
from spade import wait_until_finished


async def main():
    env = Environment()
    stockmarket_agent = StockMarketAgent("stockmarket@localhost", "", env)
    await stockmarket_agent.start()
    env.load_from_file()

    trading_agent = StockTradingAgent("trading_agent@localhost", "", env)
    await trading_agent.start()

    broker = Broker("broker@localhost", "", env)
    await broker.start()

    broker_agent = BrokerAgent("broker_agent@localhost", "", env)
    await broker_agent.start()

    broker_agent2 = BrokerAgent2("broker_agent2@localhost", "", env)
    await broker_agent2.start()

    random_agent = RandomAgent("random_agent@localhost", "", env)
    await random_agent.start()

    high_risk_agent = HighRiskAgent("altorisco@localhost", "", env)
    await high_risk_agent.start()

    await wait_until_finished(stockmarket_agent)
    await wait_until_finished(trading_agent)
    await wait_until_finished(broker)
    await wait_until_finished(broker_agent)
    await wait_until_finished(broker_agent2)
    await wait_until_finished(random_agent)
    await wait_until_finished(high_risk_agent)


if __name__ == "__main__":
    asyncio.run(main())
