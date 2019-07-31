# Remove in future: currently allows us to import netQuil
import sys
sys.path.insert(0, '/Users/zacespinosa/Foundry/netQuil')
sys.path.insert(1, '/Users/matthewradzihovsky/documents/netQuil')

from pyquil import Program
from pyquil.api import WavefunctionSimulator, QVMConnection
from pyquil.gates import *
from netQuil import *

def printWF(p):
    '''
    Prints the wavefunction from simulating a program p
    '''
    wf_sim = WavefunctionSimulator()
    waveFunction = wf_sim.wavefunction(p)
    print(waveFunction)
    

class Charlie(Agent):
    '''
    Charlie sends Bell pairs to Alice and Bob
    '''
    def run(self):

        # Create Bell State Pair
        p = self.program
        p += H(0)
        p += CNOT(0,1)

        self.qsend(alice.name, [0])
        self.qsend(bob.name, [1])

class Alice(Agent): 
    '''
    Alice projects her state on her Bell State Pair from Charlie
    '''
    def run(self): 
        p = self.program

        # Define Alice's Qubits
        phi = self.qubits[0]
        qubitsCharlie = self.qrecv(charlie.name)
        a = qubitsCharlie[0]

        # Entangle Ancilla and Phi
        p += CNOT(phi, a)
        p += H(phi)

        # Measure Ancilla and Phi
        p += MEASURE(a, ro[0])
        p += MEASURE(phi, ro[1])
    

class Bob(Agent): 
    '''
    Bob recreates Alice's state based on her measurements
    '''
    def run(self):
        p = self.program

        # Define Bob's qubits
        qubitsCharlie = self.qrecv(charlie.name)
        b = qubitsCharlie[0]

        # Prepare State Based on Measurements
        p.if_then(ro[0], X(b))
        p.if_then(ro[1], Z(b))


p = Program()

# Prepare psi
p += H(2)
p += Z(2)
p += RZ(1.2, 2)
print("Initial Alice State: ")
printWF(p)

# Create Classical Memory
ro = p.declare('ro', 'BIT', 3)

# Create Alice, Bob, and Charlie. Give Alice qubit 2 (phi). Give Charlie qubits [0,1] (Bell State Pairs). 
alice = Alice(p, qubits=[2], name='alice')
bob = Bob(p, name='bob')
charlie = Charlie(p, qubits=[0,1], name='charlie')

# Connect agents to distribute qubits and report results
QConnect(alice, charlie, bob)
CConnect(alice, bob)

# Run simulation
Simulation(alice, bob, charlie).run(trials=1, agent_classes=[Alice, Bob, Charlie])
qvm = QVMConnection()
qvm.run(p)
print("Final Bob's State: ")
printWF(p)
