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
    def __init__(self, unique_id, model, cash, inventory, strategy):
        super().__init__(unique_id, model)
        self.cash = cash
        self.inventory = inventory
        self.inventory_limit = inventory
        self.last_price = model.current_price
        self.strategy = strategy
    
    # Calculate the amount to buy based on the current price
    def calculate_buy_amount(self, price):
        if price < self.last_price:
            return int((self.cash * 0.9) / price)
        else:
            return 0

    # Calculate the amount to sell based on the current price
    def calculate_sell_amount(self, price):
        if price > self.last_price:
            return self.inventory // 2
        else:
            return 0
           
    # Execute a buy order
    def buy(self, amount, price):
        cost = amount * price
        if cost <= self.cash:
            self.cash -= cost
            self.inventory += amount
    
    # Execute a sell order
    def sell(self, amount, price):
        proceeds = amount * price
        if amount <= self.inventory:
            self.cash += proceeds
            self.inventory -= amount

    # Define the agent's behavior at each step
    def step(self):
        # Update the last price
        self.last_price = self.model.current_price

        # Calculate buy and sell orders
        buy_amount = self.calculate_buy_amount(self.last_price)
        sell_amount = self.calculate_sell_amount(self.last_price)
        
        # Execute buy and sell orders
        self.buy(buy_amount, self.last_price)
        self.sell(sell_amount, self.last_price)    

        # Move the agent
        self.move()   

        # Trade with neighbors
        self.trade()
    
    # Move the agent to one of the adjacent cells
    def move(self):
        # Get possible neighbors
        possible_steps = self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=False)

        # Find adjacent cell that is not occupied by another agent
        new_position = None
        possible_adjacent_cells = []
        for cell in possible_steps:
            if self.model.grid.is_cell_empty(cell):
                # If the cell is empty, add it to the list of possible cells
                possible_adjacent_cells.append(cell)

        # Select a random cell from the list of possible cells
        if len(possible_adjacent_cells) > 0:
            new_position = random.choice(possible_adjacent_cells)
        
        # Otherwise, stay in the current cell
        else:
            new_position = self.pos
        
        # Move the agent to the new position
        if new_position is not None:
            self.model.grid.move_agent(self, new_position)

    # Checks wheteher there are any neighbors in the adjacent cells
    def is_neighbor(self):
        # Get possible neighbors
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True)

        # Check if there are any neighbors
        for neighbor in neighbors:
            if isinstance(neighbor, Agent):
                return True
        
        # If there are no neighbors, return False
        return False

    def trade(self):
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True)
        for neighbor in neighbors:
            if isinstance(neighbor, Trader):
                # If the neighbor has more inventory than the current agent, buy from the neighbor
                if neighbor.inventory > self.inventory:
                    buy_amount = self.calculate_buy_amount(neighbor.last_price)
                    self.buy(buy_amount, neighbor.last_price)
                    neighbor.sell(buy_amount, neighbor.last_price)
                    print("Buy amount: " + str(buy_amount) + " Neighbor inventory: " + str(neighbor.inventory) + " Neighbor cash: " + str(neighbor.cash) + " Neighbor last price: " + str(neighbor.last_price))
                # If the neighbor has less inventory than the current agent, sell to the neighbor
                elif neighbor.inventory < self.inventory:
                    sell_amount = self.calculate_sell_amount(neighbor.last_price)
                    self.sell(sell_amount, neighbor.last_price)
                    neighbor.buy(sell_amount, neighbor.last_price)
                    print("Sell amount: " + str(sell_amount) + " Neighbor inventory: " + str(neighbor.inventory) + " Neighbor cash: " + str(neighbor.cash) + " Neighbor last price: " + str(neighbor.last_price))
                # If the neighbor has the same inventory as the current agent, do nothing
                else:
                    pass

# Define the model class
class TraderModel(Model):
    # Define the model's initial state
    def __init__(self, num_traders, width, height, initial_price, cash_per_trader, inventory_per_trader, strategy):
        self.num_traders = num_traders
        self.current_price = initial_price
        self.grid = MultiGrid(width, height, False)
        self.schedule = RandomActivation(self)

        # Define the data collector
        self.datacollector = DataCollector(
            model_reporters={"Price": "current_price"},
            agent_reporters={"Cash": "cash", "Inventory": "inventory"})

        # Create agents
        for i in range(self.num_traders):
            a = Trader(i, self, cash_per_trader, inventory_per_trader, strategy)
            self.schedule.add(a)

            # Add the agent to a random grid cell
            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))
        
    def step(self):
        # Update the current price based on market dynamics
        self.current_price = self.current_price + random.uniform(-1, 1)

        # Get all the traders and their current inventory
        traders = self.schedule.agents
        trader_inventory = [trader.inventory for trader in traders]

        # Determine the average inventory among traders
        avg_inventory = sum(trader_inventory) / len(trader_inventory)
        
        # Step all the traders in random order
        for trader in self.schedule.agents:
            #Implement a simple trend following strategy based on the current price and the average inventory
            if self.current_price > trader.last_price and trader.inventory >= avg_inventory:
                # Buy if the price is rising and the trader has more inventory than average
                buy_amount = trader.calculate_buy_amount(self.current_price)
                trader.buy(buy_amount, self.current_price)
            elif self.current_price < trader.last_price and trader.inventory <= avg_inventory:
                # Sell if the price is falling and the trader has less inventory than average
                sell_amount = trader.calculate_sell_amount(self.current_price)
                trader.sell(sell_amount, self.current_price)

        # Collect data at the end of the step
        self.datacollector.collect(self)

        # Move all the traders
        self.schedule.step()

# Define a function for visualizing the traders
def trader_portrayal(trader):
    portrayal = {"Shape": "circle",
                 "Filled": "true",
                 "r": 0.5,
                 "Color": "blue",
                 "Layer": 0,
                 "text": trader.unique_id,
                 "text_color": "black",
                 "position": (trader.pos[0], trader.pos[1])
                 }
    return portrayal

# Define a canvas grid for visualizing the trader agents
canvas_element = CanvasGrid(trader_portrayal, 10, 10, 500, 500)

# Define a chart module for visualizing the asset price
chart = ChartModule([{"Label": "Average Cash", "Color": "Green"},
                     {"Label": "Average Inventory", "Color": "Black"}],
                     data_collector_name='datacollector')

# Create the server and launch it
model_params = {
    "width": 10,
    "height": 10,
    "num_traders": UserSettableParameter('slider', 'Number of Traders', 10, 2, 20, 1),
    "initial_price": UserSettableParameter('slider', 'Initial Price', 100, 50, 150, 1),
    "cash_per_trader": UserSettableParameter('slider', 'Initial Cash', 1000, 500, 2000, 50),
    "inventory_per_trader": UserSettableParameter('slider', 'Initial Inventory', 10, 5, 20, 1),
    "strategy": UserSettableParameter('choice', 'Trading Strategy', value='Random',
                                       choices=['Random', 'Buy Low, Sell High', 'Momentum'])
}

# Create the server and launch it
server = ModularServer(TraderModel, [canvas_element, chart], "Trader Model", model_params)
server.port = 8521 # The default
server.launch()