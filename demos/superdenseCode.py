import sys
sys.path.insert(1, '/Users/matthewradzihovsky/documents/qnetdes')
sys.path.insert(0, '/Users/zacespinosa/Foundry/qnetdes')

from pyquil import Program
from pyquil.api import WavefunctionSimulator, QVMConnection
from pyquil.gates import *
from qnetdes import *

class Charlie(Agent):
    '''
    Charlie sends Bell pairs to Alice and Bob
    '''
    def run(self):
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
        
        
        if bit2 == 1: p += X(a)
        if bit1 == 1: p += Z(a)
        self.qsend(bob.name, [a])

class Bob(Agent):
    '''
    Bob reconstructs Alice's classical bits
    '''
    def run(self):
        p = self.program
        ro = p.declare('ro', 'BIT', 2)
        qubitsAlice = self.qrecv(alice.name)
        qubitsCharlie = self.qrecv(charlie.name)
        a = qubitsAlice[0]
        c = qubitsCharlie[0]

        p += CNOT(a,c)
        p += H(a)
        p += MEASURE(a, ro[0])
        p += MEASURE(c, ro[1])

qvm = QVMConnection()
program = Program()

#define agents
alice = Alice(program, cmem=[0,1])
alice.add_source_devices([Laser(apply_error=True)])
bob = Bob(program)
charlie = Charlie(program, qubits=[0,1])

#connect agents
QConnect(alice, bob, [Fiber(length=10, apply_error=False) ])
QConnect(bob, charlie)
QConnect(alice, charlie)

#simulate agents
Simulation(alice,charlie,bob).run(trials=10, agent_classes=[Alice, Charlie, Bob])
results = qvm.run(program, trials=10)
wf_sim = WavefunctionSimulator()
resultWF = wf_sim.wavefunction(program)


print('Final state: ', resultWF)
print('Alice\'s bits: ', alice.cmem)
print('Bob\'s results:', results)

print('Bob\'s time:', bob.time)
print('Alice\'s time:', alice.time)

