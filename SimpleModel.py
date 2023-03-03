from mesa import Agent
from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.modules import ChartModule
import random

# Define the agent class
class Trader(Agent):
    # Define the agent's initial state
    def __init__(self, unique_id, model, cash, inventory, trading):
        super().__init__(unique_id, model)
        self.cash = cash
        self.inventory = inventory
        self.trading = trading

    # Define the agent's step functions
    def step(self):
        # Move the agent to a new cell
        self.move()

        # Check for neighboring agents and trade with them if possible
        neighbors = self.model.grid.get_neighbors(self.pos, moore=False, include_center=False, radius=1)
        for neighbor in neighbors:
            if isinstance(neighbor, Trader):
                self.trade(neighbor)

    # Move the agent to one of the adjacent cells
    def move(self):
        # Get possible neighbors
        possible_steps = self.model.grid.get_neighborhood(
            self.pos,
            moore=False,
            include_center=False,
            radius=1)

        # Find adjacent cell that is not occupied by another agent
        possible_adjacent_cells = [cell for cell in possible_steps if self.model.grid.is_cell_empty(cell)]

        # Exit early if there are no possible adjacent cells
        if not possible_adjacent_cells:
            return

        # Select a random cell from the list of possible cells
        new_position = random.choice(possible_adjacent_cells)

        # Move the agent to the new position
        self.model.grid.move_agent(self, new_position)
    
    # Define the agent's interaction method
    def trade(self, other):
        # Define the interaction logic here
        # For example, you could have the traders negotiate a trade based on their inventory and cash
        pass

# Define the model class
class TraderModel(Model):
    # Define the model's initial state
    def __init__(self, num_traders, width, height, initial_price, initial_inventory, cash_per_trader, inventory_per_trader):
        self.num_traders = num_traders
        self.current_price = initial_price
        self.schedule = RandomActivation(self)

        # Create a grid
        self.grid = MultiGrid(width, height, False)

        # Create data collector
        self.datacollector = DataCollector(
            model_reporters={"Price": "current_price"},
            agent_reporters={"Cash": "cash", "Inventory": "inventory"}
        )
        
        # For each trader, create a new agent and place it in a random cell
        for i in range(self.num_traders):
            
            # Create a new trader
            a = Trader(i, self, cash_per_trader, inventory_per_trader, False)
            self.schedule.add(a)

            # Add the agent to a random grid cell
            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            
            # If the cell is not empty, select a new cell
            while not self.grid.is_cell_empty((x, y)):
                x = random.randrange(self.grid.width)
                y = random.randrange(self.grid.height)

            # Place the agent in the selected cell
            self.grid.place_agent(a, (x, y))

    # Define the model's step function   
    def step(self):

        # Collect data
        self.datacollector.collect(self)

        # Execute the step function for each agent
        self.schedule.step()        

# Define a function for visualizing the traders
def agentPortrayal(trader):

    portrayal = {"Shape": "circle",
                 "Filled": "true",
                 "r": 0.5,
                 "Color": "blue",
                 "Layer": 0,
                 "text": trader.unique_id,
                 "text_color": "black"
                 }
    return portrayal

# Define a canvas grid for visualizing the trader agents
canvas = CanvasGrid(agentPortrayal, 10, 10, 500, 500)

# Create the server and launch it
model_params = {
    "width": 10,
    "height": 10,
    "num_traders": UserSettableParameter('slider', 'Number of Traders', 10, 2, 20, 1),
    "initial_price": UserSettableParameter('slider', 'Initial Price', 100, 50, 150, 1),
    "initial_inventory": UserSettableParameter('slider', 'Initial Inventory', 10, 5, 20, 1),
    "cash_per_trader": UserSettableParameter('slider', 'Initial Cash', 1000, 500, 2000, 50),
    "inventory_per_trader": UserSettableParameter('slider', 'Initial Inventory', 10, 5, 20, 1),
}

# Create server
server = ModularServer(TraderModel, [canvas], "Trader Model", model_params)

# Launch server
server.launch()