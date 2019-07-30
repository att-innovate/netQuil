# Remove in future: currently allows us to import qnetdes
import sys
sys.path.insert(0, '/Users/zacespinosa/Foundry/qnetdes')
sys.path.insert(1, '/Users/matthewradzihovsky/documents/qnetdes')

from pyquil import Program
from pyquil.api import WavefunctionSimulator, QVMConnection
from pyquil.gates import *
from qnetdes import *

def printWF(t, p):
    '''
    Prints the wavefunction from simulating a program p
    '''
    wf_sim = WavefunctionSimulator()
    waveFunction = wf_sim.wavefunction(p)
    print(t, waveFunction)

class Alice(Agent): 
    '''
    Alice uses cat-entangler to perform distributed quantum teleportation
    '''
    def teleportation(self, phi, a, b):
        cat_entangler(
            control=(self, phi, a, ro),
            targets=[(bob, b)],
            entangled=False,
            notify=True
        )
        cat_disentangler(
            control=(bob, b, ro),
            targets=[(self, phi)],
            notify=True
        )

    def run(self):
        a, phi = self.qubits 
        b = bob.qubits[0]
        self.teleportation(phi, a, b)

class Bob(Agent): 
    '''
    Bob uses cat-disentangled to perform distributed quantum teleportation
    '''
    def run(self):
        self.crecv(alice.name)
        self.crecv(alice.name)

p = Program()

# Prepare psi
p += H(2)
p += Z(2)
p += RZ(1.2, 2)
print('Alice has Qubits 0 and 2, Bob has qubit 1')
printWF('Before Teleportation: ', p)

# Create Classical Memory
ro = p.declare('ro', 'BIT', 3)

# Create Alice, Bob, and Charlie. Give Alice qubit 2 (phi). Give Charlie qubits [0,1] (Bell State Pairs). 
alice = Alice(p, qubits=[0,2], name='alice')
bob = Bob(p, qubits=[1], name='bob')

# Connect agents to distribute qubits and report results
QConnect(alice, bob)
CConnect(alice, bob)

Simulation(alice, bob).run()
qvm = QVMConnection()
qvm.run(p)
printWF('After Teleportation: ', p)