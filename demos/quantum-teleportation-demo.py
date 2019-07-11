# Remove in future: currently allows us to import qnetdes
import sys
sys.path.insert(0, '/Users/zacespinosa/Foundry/qnetdes')
sys.path.insert(1, '/Users/matthewradzihovsky/documents/qnetdes')

from pyquil import Program
from pyquil.api import WavefunctionSimulator, QVMConnection
from pyquil.gates import *
from qnetdes import *

def printWF(p):
    wf_sim = WavefunctionSimulator()
    waveFunction = wf_sim.wavefunction(p)
    print(waveFunction)
    
class Alice(Agent): 
    def run(self): 
        # Define Alice's qubits
        a, phi = self.qubits
        p = self.program

        # Entangle Ancilla and Phi
        p += CNOT(phi, a)
        p += H(phi)

        # Measure Ancilla and Phi
        p += MEASURE(a, ro[0])
        p += MEASURE(phi, ro[1])
    
        # Send Cbits
        bits = [0,1]
        self.csend('bob', bits)

class Bob(Agent): 
    def run(self):
        b = self.qubits[0]
        self.crecv('alice')

        p = self.program
        p.if_then(ro[0], X(b))
        p.if_then(ro[1], Z(b))

# Create Phi
p = Program(H(2))
printWF(p)

# Entangle qubits 0 and 1. 
p += Program(H(0))
p += CNOT(0,1) 

# Create Classical Memory
ro = p.declare('ro', 'BIT', 3)

# Create Alice and Bob. Give Alice qubit 0 (ancilla) and qubit 2 (phi). Give Bob qubit 1
alice = Alice(p, qubits=[0, 2], name='alice')
bob = Bob(p, qubits=[1], name='bob')

# Connect Alice and Bob via a quantum connection and classical connection with no transit devices
QConnect(alice, bob)
CConnect(alice, bob)

# Run simulation
Simulation(alice, bob).run(trials=4, agent_classes=[Alice, Bob])
qvm = QVMConnection()
qvm.run(p)
printWF(p)
