# Remove in future: currently allows us to import netQuil
import sys
sys.path.insert(0, '/Users/zacespinosa/Foundry/netQuil')
sys.path.insert(1, '/Users/matthewradzihovsky/documents/netQuil')

from pyquil import Program
from pyquil.api import WavefunctionSimulator, QVMConnection
from pyquil.gates import *
from netQuil import *

'''
Goal: Alice has a qubit Phi which Bob would like to use as a control bit for 
    a series of operations. 

Procedure: Alice creates a pair of entangled qubits, keeps qubit A, and sends
    qubit B to Bob. Alice and Bob then use the cat_entangler to transfer Alice's local 
    control bit to Bob. Bob performs a series of transformations on his qubits using Phi 
    as a control bit. Alice and Bob then use cat_disentangler to return qubits to original
    state. This procedure is alson known as the non-local CNOT
'''

def printWF(p):
    wf_sim = WavefunctionSimulator()
    waveFunction = wf_sim.wavefunction(p)
    print(waveFunction)

class Alice(Agent): 
    def cat_disentangler(self, p): 
        done = self.crecv(bob.name) 
        if done: 
            self.crecv(bob.name) 
            p.if_then(ro[1], Z(0))
            p += MEASURE(0, ro[0])

    def cat_entangler(self, p):
        p += CNOT(2,0)
        p += MEASURE(0, ro[0])
        p.if_then(ro[0], X(0))
        
        p += MEASURE(2, ro[2])

    def entangle_pair(self, p):
        p += H(0)
        p += CNOT(0, 1)
        # Distribute 1st qubit to Bob
        self.qsend(bob.name, [1])

    def run(self):
        p = self.program
        self.entangle_pair(p)
        self.cat_entangler(p)
        self.cat_disentangler(p)

class Bob(Agent):
    def get_entangle_pair(self, p):
        self.qrecv(alice.name)

    def cat_entangler(self, p): 
        # Receive measurment
        self.crecv(alice.name)
        p.if_then(ro[0], X(1))

        p += CNOT(1, 3)
        p += MEASURE(3, ro[3]) 

    def cat_disentangler(self, p):
        # Tell alice we done
        self.csend(alice.name, [1]) 
        p += H(1)
        p += MEASURE(1, ro[1])
        p.if_then(ro[1], X(1))
        
        p += MEASURE(1, ro[1])

    def run(self):
        p = self.program
        self.get_entangle_pair(p)
        self.cat_entangler(p)
        self.cat_disentangler(p)

qvm = QVMConnection()
program = Program(I(0),I(1), X(2), X(3))
ro = program.declare('ro', 'BIT', 4)
printWF(program)

# Define Agents
alice = Alice(program, qubits=[0,1,2]) 
bob = Bob(program, qubits=[3])

# Connect Agents
QConnect(alice, bob)
CConnect(alice, bob)

# Run Simulation
Simulation(alice, bob).run(trials=1)
results = qvm.run(program)
printWF(program)