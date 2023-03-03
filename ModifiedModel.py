from mesa import Model
from mesa.agent import Agent
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.modules import ChartModule
from mesa.visualization.UserParam import UserSettableParameter

class Trader(Agent):
    def __init__(self, unique_id, model, wealth, price):
        super().__init__(unique_id, model)
        self.wealth = wealth
        self.price = price
    
    def step(self):
        # Agent behaviour
        """if self.wealth <= 0:
            self.model.schedule.remove(self)
            return

        if self.random.random() < 0.5:
            self.buy()
        else:
            self.sell()"""

        self.sell()
        self.move()
        
        #self.move()
        #self.trade()
    
    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=False)
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

    def trade(self):
        neighbors = self.model.grid.get_neighbors(self.pos, include_center=False, moore=True)
        for neighbor in neighbors:
            if self.price <= neighbor.price and self.wealth > self.price:
                self.wealth -= self.price
                neighbor.wealth += self.price
                self.model.total_transactions += 1

    def buy(self):
        neighbors = self.model.grid.get_neighbors(self.pos, include_center=False, moore=True)
        if not neighbors:
            return

        # Choose a seller at random
        seller = self.random.choice(neighbors)
        if seller.price > self.price:
            return
        
        cost = seller.price
        if self.wealth >= cost:
            seller.wealth += cost
            self.wealth -= cost
            self.model.grid.move_agent(self, seller.pos)
            self.model.total_transactions += 1

        """if self.wealth >= self.price:
            neighbors = self.model.grid.get_neighbors(self.pos, include_center=False, moore=True)
            if len(neighbors) > 0:
                seller = self.random.choice(neighbors)
                if seller.price <= self.price:
                    self.wealth -= self.price
                    seller.wealth += self.price
                    self.model.total_transactions += 1"""

    def sell(self):

        # Look for a neighboring cell with a buyer

        neighbors = self.model.grid.get_neighbors(self.pos, include_center=False, moore=True)
        buyers = [agent for agent in self.model.grid.get_cell_list_contents(neighbors) if isinstance(agent, Trader) and agent.price >= self.price]

        if buyers:
            # Choose a random buyer from the neighboring cells and sell to them
            buyer = self.random.choice(buyers)
            buyer.wealth -= self.price
            self.wealth += self.price
            self.model.total_transactions += 1

        """neighbors = self.model.grid.get_neighbors(self.pos, include_center=False, moore=True)
        if not neighbors:
            return
        
        # Choose a buyer at random
        buyer = self.random.choice(neighbors)
        if buyer.price < self.price:
            return

        price = self.price
        if buyer.wealth >= price:
            buyer.wealth -= price
            self.wealth += price
            self.model.grid.move_agent(self, buyer.pos)
            self.model.total_transactions += 1"""

        """if self.wealth >= 0:
            neighbors = self.model.grid.get_neighbors(self.pos, include_center=False, moore=True)
            if len(neighbors) > 0:
                buyer = self.random.choice(neighbors)
                if buyer.price >= self.price:
                    self.wealth += self.price
                    buyer.wealth -= self.price
                    self.model.total_transactions += 1"""

def total_wealth(model):
    return sum([a.wealth for a in model.schedule.agents])

def total_transactions(model):
    return model.stions

class FinanceModel(Model):
    def __init__(self, N, width, height):
        self.num_agents = N
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)
        self.total_transactions = 0
        self.datacollector = DataCollector(
            model_reporters={"Total_Wealth": total_wealth, "Total_Transactions": total_transactions},
            agent_reporters={"Wealth": lambda a: a.wealth, "Price": lambda a: a.price})
        
        # Create agents
        for i in range(self.num_agents):
            a = Trader(i, self, 100, self.random.randrange(1, 10))
            self.schedule.add(a)

            # Add the agent to a random grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)

def agent_portrayal(agent):
    portrayal = {"Shape": "circle",
                 "Filled": "true",
                 "r": 0.5,
                 "Layer": 0,
                 "Color": "red" if agent.price > 5 else "green"}
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
    "height": 10
}

server = ModularServer(FinanceModel,
                            [grid, chart],
                            "Finance Model",
                            model_params)

server.port = 8521 # The default
server.launch()