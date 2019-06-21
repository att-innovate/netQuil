# Remove in future: currently allows us to import qnetdes
import sys
sys.path.insert(0, '/Users/zacespinosa/Foundry/qnetdes')

from qnetdes import *
from pyquil import Program
from pyquil.gates import *
from pyquil.api import WavefunctionSimulator

p = Program(H(0), CNOT(0,1))

class Alice(Agent): 
    def run(self): 
        print(self.qubits)
        self.qsend('bob',[1])
        print(self.qubits)

class Bob(Agent): 
    def run(self):
        print(self.qubits) 
        self.qrecv('alice')
        print(self.qubits) 
        
alice = Alice(p, [0,1], 'alice')
bob = Bob(p, [1, 2], 'bob')

QConnect(alice, bob, [None])
Simulation(alice, bob).run()