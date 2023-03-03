from mesa import Agent
from mesa.space import ContinuousSpace
import numpy as np
import random

class MyAgent(Agent):
    def __init__(self, unique_id, pos, model):
        super().__init__(unique_id, model)
        self.pos = pos

    def move(self):
        # move randomşy in the space
        x = self.pos + self.random.uniform(-1, 1)
        y = self.pos + self.random.uniform(-1, 1)
        self.model.space.move_agent(self, (x, y))

    def interact(self):
        # find neigboring agents within a certain distance
        neighbors = self.model.space.get_neighbors(self.pos, 1, include_center=False)
        for neighbor in neighbors:
            # calculate the distance between the two agents
            distance = self.model.space.get_distance(self.pos, neighbor.pos)
            if dist <= 1:
                # do something
                print ("Agent {} is interacting with agent {}".format(self.unique_id, neighbor.unique_id))

# create a model with a continuos space

class MyModel:
    def __init__(self):
        self.space = ContinuousSpace(10, 10, torus=True)
        self.agents = [MyAgent(i, self.get_random_pos(), self) for i in range(10)]
        self.running = True

    def step(self):
        for agent in self.agents:
            agent.move()
            agent.interact()
    
    def get_random_pos(self):
        x = np.random.uniform(0, self.space.width)
        y = np.random.uniform(0, self.space.height)
        return (x, y)

# create and run the model
model = MyModel()
while model.running:
    model.step() 