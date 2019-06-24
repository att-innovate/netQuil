# Remove in future: currently allows us to import qnetdes
import sys
import threading 
sys.path.insert(0, '/Users/zacespinosa/Foundry/qnetdes')

from qnetdes import *
from pyquil import Program
from pyquil.gates import *
from pyquil.api import WavefunctionSimulator

class Alice(Agent):
    def run(self):
        self.program += Z(0)
        print('alice', self.program)

class Bob(Agent):
    def run(self):
        self.program += X(0)
        print('Bob', self.program)

p = Program(H(0)) 
ro = p.declare('ro', 'BIT', 3)
alice = Alice(p, [0, 2], 'alice')
bob = Bob(p, [1], 'bob')

QConnect(alice, bob, [None])
CConnect(alice, bob)
Simulation(alice, bob).run()