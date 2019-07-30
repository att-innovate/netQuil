# Remove in future: currently allows us to import qnetdes
import sys
sys.path.insert(0, '/Users/zacespinosa/Foundry/qnetdes')
sys.path.insert(1, '/Users/matthewradzihovsky/documents/qnetdes')

from pyquil import Program
from pyquil.api import WavefunctionSimulator, QVMConnection
from pyquil.gates import *
from qnetdes import *

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
        p += CNOT(0, 1)

        self.qsend(bob.name, [1])
        self.qsend(alice.name, [0])

class Alice(Agent): 
    '''
    Alice uses cat-entangler to perform distributed quantum teleportation
    '''
    def run(self):
        p = self.program

        # Define Qubits
        phi = self.qubits[0]
        qubitsCharlie = self.qrecv(charlie.name)
        a = qubitsCharlie[0]
        b = 1

        # Use cat-entangler
        cat_entangler(
            control=(phi, ro),
            measure=a,
            targets=[b],
            caller=self,
            entangled=True
        ) 

class Bob(Agent): 
    '''
    Bob uses cat-disentangled to perform distributed quantum teleportation
    '''
    def run(self):
        p = self.program
        # Define Qubits
        qubitsCharlie = self.qrecv(charlie.name)
        b = qubitsCharlie[0]
        phi = alice.qubits[1]

        # Use cat_disentangler
        cat_disentangler(
            control=(b, ro),
            targets=[phi],
            caller=self,
        )

p = Program()

# Prepare psi
p += H(2)
p += Z(2)
p += RZ(1.2, 2)
printWF(p)

# Create Classical Memory
ro = p.declare('ro', 'BIT', 3)

# Create Alice, Bob, and Charlie. Give Alice qubit 2 (phi). Give Charlie qubits [0,1] (Bell State Pairs). 
alice = Alice(p, qubits=[2,0], name='alice')
bob = Bob(p, name='bob')
charlie = Charlie(p, qubits=[0,1], name='charlie')

# Connect agents to distribute qubits and report results
QConnect(alice, charlie)
QConnect(bob, charlie)
QConnect(alice, bob)
CConnect(alice, bob)

Simulation(alice, bob, charlie).run()
qvm = QVMConnection()
qvm.run(p)
printWF(p)
print(p)