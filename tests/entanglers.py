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

def test_entangler(agent):
    # cbit from measurement of cat_entangler
    agent.crecv(alice.name)
    #  cbit indicating Alice is done with cat_entangler
    agent.crecv(alice.name)

    # Perform work with qubit that alice has projected her control onto
    control_bit, target_bit = agent.qubits[0], agent.qubits[1]
    p = agent.program
    p += CNOT(control_bit, target_bit)

    # Tell Alice we are done
    agent.csend(alice.name, [1])

class Alice(Agent): 
    def run(self):
        q = self.qubits
        a, phi = q[0], q[1]

        # Perform cat _entangler
        cat_entangler(
            control=(self, phi, a, ro),
            targets=[(bob, 1), (charlie, 2), (don, 3), (eve, 4)],
            entangled=True,
            notify=True
        )
        # Wait until Agents are done working
        for agent in agents[1:]: self.crecv(agent.name)
        printWF(self.program)
        # Perform cat_disentangler
        cat_disentangler(
           control=(self, phi, ro),
           targets=[(bob, 1), (charlie, 2), (don, 3), (eve, 4)],
           notify=False
        )

class Bob(Agent): 
    def run(self):
        test_entangler(self)

class Don(Agent):
    def run(self):
        test_entangler(self)

class Eve(Agent):
    def run(self): 
        test_entangler(self)

class Charlie(Agent):
    def run(self):
        test_entangler(self)

p = Program()

# Prepare 5 qubit entangled system
p += H(0)
p += CNOT(0,1)
p += CNOT(0,2)
p += CNOT(0,3)
p += CNOT(0,4)

# Prepare psi 
p += H(5)
printWF(p)

# Create Classical Memory
ro = p.declare('ro', 'BIT', 5)

# Create Agent
alice = Alice(p, qubits=[0,5], name='alice')
bob = Bob(p, qubits=[1,6], name='bob')
charlie = Charlie(p, qubits=[2,7], name='charlie')
don = Don(p, qubits=[3,8], name='don')
eve = Eve(p, qubits=[4,9], name='eve')

# Connect Agents 
agents = [alice, bob, charlie, don, eve]

for i in range(len(agents) - 1):
    for j in range(i+1, len(agents)):
        QConnect(agents[i], agents[j])
        CConnect(agents[i], agents[j])

Simulation(alice, bob, charlie, don, eve).run()
qvm = QVMConnection()
qvm.run(p)
printWF(p)