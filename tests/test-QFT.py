import sys
import math
sys.path.insert(0, '/Users/zacespinosa/Foundry/netQuil')
sys.path.insert(1, '/Users/matthewradzihovsky/documents/netQuil')

from pyquil import Program
from pyquil.gates import *
from pyquil.api import WavefunctionSimulator, QVMConnection
from netQuil import *

''' 
    Simple manual test for Quantum Fourier Transform
'''
class Alice(Agent): 
    def run(self): 
        p = self.program
        print("IN ALICE")
        distributed_gates.QFT(p, self.qubits)

p = Program()
p = p.inst(H(0), H(1), H(2), H(3), H(4))

# Create Alice and Bob. Give Alice qubit 0 (ancilla) and qubit 2 (phi). Give Bob qubit 1
alice = Alice(p, [0, 1, 2, 3, 4], [], 'alice')

# Connect Alice and Bob via a quantum connection and classical connection with no transit devices
#QConnect(alice, bob, transit_devices=[None])

# Run simulation
Simulation(alice).run(trials=1, agent_classes=[Alice])
print('Amplitudes using QFT: {}'.format(WavefunctionSimulator().wavefunction(p).amplitudes))
print(p)
