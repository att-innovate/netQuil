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
        
        #noise from attenuation
        if a is not None:
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

        #noise from attenuation
        if a is not None and c is not None:
            p += CNOT(a,c)
            p += H(a)
            p += MEASURE(a, ro[0])
            p += MEASURE(c, ro[1])

qvm = QVMConnection()
program = Program()
alice = Alice(program, qubits=[], cmem=[0,1])
bob = Bob(program, qubits=[])
charlie = Charlie(program, qubits=[0,1])

QConnect(alice, bob, transit_devices=[])
QConnect(bob, charlie, transit_devices=[])
QConnect(alice, charlie, transit_devices=[])

Simulation(alice,charlie,bob).run()
results = qvm.run(program)
wf_sim = WavefunctionSimulator()
resultWF = wf_sim.wavefunction (program)
print('Final state: ', resultWF)
print('Alice\'s bits: ', alice.cmem)
print('Bob\'s results:', results)