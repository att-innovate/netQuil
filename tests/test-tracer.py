import sys
import threading 
import inspect
sys.path.insert(0, '/Users/zacespinosa/Foundry/netQuil')
sys.path.insert(1, '/Users/matthewradzihovsky/documents/netQuil')

from netQuil import *
from pyquil import Program
from pyquil.gates import *
from pyquil.api import WavefunctionSimulator, QVMConnection

''' 
    Simple manual test of tracer. Tracer prevents agents from modifying or sending qubits they do not own and manage
'''
class Alice(Agent): 
    def run(self): 
        a, c = self.qubits
        p = self.program
        p += CNOT(c, a)
        p += H(c)

        # Send qubit c
        self.qsend('bob', [c])

class Bob(Agent): 
    def run(self):
        p = self.program
        c = 2
        # Try modifying qubit c before receiving from Alice
        try:
            p += H(c)
        except: 
            print('Tried to modify qubit c, before receiving from Alice and failed')

        # Receive qubit c
        qubits = self.qrecv('alice')

        # Modify qubit c after receiving
        p += H(c)
        print('Successfully modified qubit c after receiving')
        
        qvm = QVMConnection()
        result = qvm.run(p)

# Create Phi
p = Program(H(2)) 
# Entangle qubits 0 and 1. 
p += Program(H(0))
p += CNOT(0,1) 

# Create Alice and Bob. Give Alice qubit 0 (ancilla) and qubit 2 (phi). Give Bob qubit 1
alice = Alice(p, [0, 2], [], 'alice')
bob = Bob(p, [1], [], 'bob')

# Connect Alice and Bob via a quantum connection and classical connection with no transit devices
QConnect(alice, bob, transit_devices=[None])

# Run simulation
Simulation(bob, alice).run()