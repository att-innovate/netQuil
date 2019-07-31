import sys
sys.path.insert(1, '/Users/matthewradzihovsky/documents/netQuil')
sys.path.insert(0, '/Users/zacespinosa/Foundry/netQuil')

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
    Alice sends Bob superdense-encoded classical bits
    '''
    def run(self):
        p = self.program
        qubitsCharlie = self.qrecv(charlie.name)
        a = qubitsCharlie[0]
        
        bit1 = self.cmem[0]
        bit2 = self.cmem[1]
        
        # Operate on Qubit depending on Classical Bit
        if bit2 == 1: p += X(a)
        if bit1 == 1: p += Z(a)
        self.qsend(bob.name, [a])

class Bob(Agent):
    '''
    Bob reconstructs Alice's classical bits
    '''
    def run(self):
        p = self.program

        # Get Qubits from Alice and Charlie
        qubitsAlice = self.qrecv(alice.name)
        qubitsCharlie = self.qrecv(charlie.name)
        a = qubitsAlice[0]
        c = qubitsCharlie[0]

        p += CNOT(a,c)
        p += H(a)
        p += MEASURE(a, ro[0])
        p += MEASURE(c, ro[1])

program = Program()

# Create Classical Memory
ro = program.declare('ro', 'BIT', 2)

# Define Agents
alice = Alice(program, cmem=[0,1])
alice.add_source_devices([Laser(apply_error=True)])
bob = Bob(program)
charlie = Charlie(program, qubits=[0,1])

# Connect Agents
QConnect(alice, bob, charlie, transit_devices=[Laser(apply_error=False)])

# Simulate Agents
Simulation(alice,charlie,bob).run(trials=1, agent_classes=[Alice, Charlie, Bob])
qvm = QVMConnection()
results = qvm.run(program)
printWF(program)


# Print Results
print('Alice\'s inital bits: ', alice.cmem)
print('Bob\'s results:', results)

