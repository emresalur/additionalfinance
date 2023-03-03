from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import random

from mesa.visualization.modules import ChartModule
from mesa.visualization.modules import TextElement
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.modules import ChartModule

class FinanceTraderModel(Model):
    def __init__(self, num_traders, initial_market_price, initial_market_volume):
        self.schedule = RandomActivation(self)
        self.market_price = initial_market_price
        self.market_volume = initial_market_volume
        self.datacollector = DataCollector(
            model_reporters={"MarketPrice": lambda m: m.market_price,
                             "MarketVolume": lambda m: m.market_volume},
            agent_reporters={"Wealth": lambda a: a.wealth})

        # Create trader agents and add them to the schedule
        for i in range(num_traders):
            trader = Trader(i, self)
            self.schedule.add(trader)

    def step(self):
        self.schedule.step()

        # Update the market price and volume based on the trading activity of the agents
        self.market_price = self.calculate_market_price()
        self.market_volume = max(self.market_volume, 0)

    def calculate_market_price(self):
        # Calculate the market price based on supply and demand
        if self.market_volume == 0:
            return self.market_price
        else:
            excess_demand = sum([a.demand for a in self.schedule.agents if isinstance(a, Trader)])
            excess_supply = sum([a.supply for a in self.schedule.agents if isinstance(a, Trader)])
            equilibrium_price = self.market_price + (excess_demand - excess_supply) / self.market_volume
            return equilibrium_price

class Trader(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.wealth = 1000
        self.bid_price = random.uniform(0.8, 1.2) * model.market_price
        self.ask_price = random.uniform(0.8, 1.2) * model.market_price
        self.demand = 0
        self.supply = 0

    def step(self):
        # Decide on a trading strategy based on market conditions
        if self.model.market_price < self.bid_price:
            # Buy assets if the price is below the trader's bid price
            self.demand = random.randint(1, 5)
            self.buy_assets(self.demand)
        elif self.model.market_price > self.ask_price:
            # Sell assets if the price is above the trader's ask price
            self.supply = random.randint(1, 5)
            self.sell_assets(self.supply)

    def buy_assets(self, quantity):
        # Buy assets at the market price if the trader's bid price is not met
        if self.model.market_price > self.bid_price:
            cost = self.model.market_price * quantity
            if self.wealth >= cost:
                self.wealth -= cost
                self.model.market_volume += quantity

    def sell_assets(self, quantity):
        # Sell assets at the market price if the trader's ask price is met
        if self.model.market_price >= self.ask_price:
            revenue = self.model.market_price * quantity
            if self.model.market_volume >= quantity:
                self.wealth += revenue
                self.model.market_volume -= quantity

# Create a visualization of the model

class MarketPriceChart(ChartModule):
    series = [{"Label": "MarketPrice", "Color": "Black"}]

class MarketVolumeChart(ChartModule):
    series = [{"Label": "MarketVolume", "Color": "Red"}]

class WealthDistributionText(TextElement):
    def render(self, model):
        wealths = [agent.wealth for agent in model.schedule.agents if isinstance(agent, Trader)]
        return "Average Wealth: {:.2f}".format(sum(wealths) / len(wealths))

def trader_portrayal(agent):
    portrayal = {"Shape": "circle",
                 "Color": "blue",
                 "Filled": "true",
                 "Layer": 1,
                 "r": 0.5}
    if agent.wealth > 500:
        portrayal["Color"] = "green"
        portrayal["r"] = 1.0
    if agent.wealth < 100:
        portrayal["Color"] = "red"
        portrayal["r"] = 0.25
    return portrayal

trader_canvas = CanvasGrid(trader_portrayal, 10, 10, 500, 500)

model_params = {"num_traders": UserSettableParameter("slider", "Number of Traders", 20, 1, 100, 1),
                "initial_market_price": UserSettableParameter("slider", "Initial Market Price", 10, 1, 100, 1),
                "initial_market_volume": UserSettableParameter("slider", "Initial Market Volume", 100, 1, 1000, 1)}

#Create the server
server = ModularServer(FinanceTraderModel,
                          [trader_canvas, MarketPriceChart, MarketVolumeChart, WealthDistributionText],
                            "Finance Trader Model",
                            model_params)
                            

server.port = 8521
server.launch()