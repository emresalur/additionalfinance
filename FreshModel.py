from mesa import Model
from mesa.agent import Agent
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.modules import ChartModule
from mesa.visualization.UserParam import UserSettableParameter
import random

class Trader(Agent):
    def __init__(self, unique_id, model, wealth, price):
        super().__init__(unique_id, model)
        self.wealth = wealth
        self.price = price

    def step(self):

        self.trade()
        self.move()

    def trade(self):
        # Get all cellmates
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        cellmates.remove(self)

        # Sort cellmates by price
        cellmates = sorted(cellmates, key=lambda x: x.price)

        # Trae with celmates in order of price
        for other in cellmates:
            if self.price < other.price:
                self.buy(other)
            elif self.price > other.price:
                self.sell(other)

    def buy(self, other):
        price = min(self.price, other.price)
        self.wealth -= price
        other.wealth += price
        self.model.total_transactions += 1

    def sell(self, other):
        price = max(self.price, other.price)
        self.wealth += price
        other.wealth -= price
        self.model.total_transactions += 1

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=False
        )
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

class FinanceModel(Model):
    def __init__(self, N, width, height, starting_wealth, starting_price):
        self.num_agents = N
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)
        self.datacollector = DataCollector(
            model_reporters={"Total_Wealth": total_wealth},
            agent_reporters={"Wealth": lambda a: a.wealth})

        # Create agents
        for i in range(self.num_agents):
            a = Trader(i, self, starting_wealth, starting_price)
            self.schedule.add(a)

            # Add the agent to a random grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()

        # Remove agent if they have no wealth
        agents_to_remove = [agent for agent in self.schedule.agents if agent.wealth <= 0]
        for agent in agents_to_remove:
            self.schedule.remove(agent)
            self.grid._remove_agent(agent.pos, agent)
            print("Removed agent " + str(agent.unique_id))

def total_wealth(model):
    return sum([a.wealth for a in model.schedule.agents])

def total_transactions(model):
    return model.total_transactions

def agent_portrayal(agent):
    portrayal = {"Shape": "circle",
                 "Filled": "true",
                 "r": 0.5,
                 "Layer": 0,
                 "Color": "red"}
    return portrayal

grid = CanvasGrid(agent_portrayal, 10, 10, 500, 500)

chart = ChartModule([{"Label": "Total_Wealth",
                        "Color": "Black"},
                        {"Label": "Total_Transactions",
                        "Color": "Blue"}],
                    data_collector_name='datacollector')

model_params = {
    "N": UserSettableParameter('slider', "Number of traders", 100, 1, 200),
    "width": 10,
    "height": 10,
    "starting_wealth": UserSettableParameter('slider', "Starting wealth", 100, 1, 1000),
    "starting_price": UserSettableParameter('slider', "Starting price", 1, 1, 10)
}

server = ModularServer(FinanceModel,
                          [grid, chart],
                            "Finance Model",
                            model_params)
                            
server.port = 8521 # The default
server.launch()