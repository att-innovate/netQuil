import sys
sys.path.insert(1, '/Users/matthewradzihovsky/documents/qnetdes')
sys.path.insert(0, '/Users/zacespinosa/Foundry/qnetdes')

from pyquil import Program
from pyquil.api import WavefunctionSimulator, QVMConnection
from pyquil.gates import *
from qnetdes import *
    
class Alice(Agent):
    '''
    Alice sends Bob superdense-encoded classical bits
    '''
    def run(self):
        p = self.program
        for i in self.qubits: 
            p += X(i)
            self.qsend(bob.name, [i])

class Bob(Agent):
    '''
    Bob reconstructs Alice's classical bits
    '''
    def run(self):
        for i in range(0, 100):
            qubitsAlice = self.qrecv(alice.name)

qvm = QVMConnection()
program = Program()

#define agents
alice = Alice(program, qubits=list(range(0, 100))) 
bob = Bob(program)

#connect agents
QConnect(alice, bob, [Fiber(length=10, apply_error=False)])

#simulate agents
Simulation(alice, bob).run()
results = qvm.run(program)

