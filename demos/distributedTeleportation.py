# Remove in future: currently allows us to import netQuil
import sys
sys.path.insert(0, '/Users/zacespinosa/Foundry/netQuil')
sys.path.insert(1, '/Users/matthewradzihovsky/documents/netQuil')

import math
from pyquil import Program
from pyquil.api import WavefunctionSimulator, QVMConnection
from pyquil.gates import *
from netQuil import *

def printWF(t, p):
    '''
    Prints the wavefunction from simulating a program p
    '''
    wf_sim = WavefunctionSimulator()
    waveFunction = wf_sim.wavefunction(p)
    print(t, waveFunction)

class Alice(Agent): 
    ''' 
    Alice uses cat-entangler and cat-disentangler to teleport psi to Bob
    '''
    def start_teleportation(self, psi, a, b):
        cat_entangler(
            control=(self, psi, a, ro),
            targets=[(bob, b)],
            entangled=False,
            notify=True
        )

    def run(self):
        # Define Qubits
        a, psi = self.qubits 
        b = bob.qubits[0]

        # Start Teleport
        self.start_teleportation(psi, a, b)

        # Wait for teleportation to finish
        cbit = self.crecv(bob.name)

class Bob(Agent): 
    ''' 
    Bob waits for cat-entangler to finish and then starts cat-disentangler
    '''
    def finish_teleportation(self, b, psi):
        cat_disentangler(
            control=(self, b, ro),
            targets=[(alice, psi)],
            notify=True
        )

    def run(self):
        # Define Qubits
        b = self.qubits[0]
        _, psi = alice.qubits

        # Receive Measurement from Cat-entangler
        self.crecv(alice.name)
        if self.crecv(alice.name)[0]: 
            self.finish_teleportation(psi, b)

p = Program()

# Prepare psi
p += H(2)
p += RZ(math.pi/2, 2)
printWF('Before', p)

# Create Classical Memory
ro = p.declare('ro', 'BIT', 3)

alice = Alice(p, qubits=[0,2], name='alice')
bob = Bob(p, qubits=[1], name='bob')

QConnect(alice, bob)
CConnect(alice, bob)

Simulation(alice, bob).run()
qvm = QVMConnection()
qvm.run(p)
printWF('After', p)