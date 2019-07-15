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
        for i in self.cmem:
            self.csend(bob.name, [i])

class Bob(Agent):
    '''
    Bob reconstructs Alice's classical bits
    '''
    def run(self):
        for i in range(100):
            cbitsAlice = self.crecv(alice.name)

qvm = QVMConnection()
program = Program()
#define agents
alice = Alice(program, cmem=[0])
for i in range(99):
    alice.add_cmem([0])
alice.add_source_devices([Laser(apply_error=True)])
bob = Bob(program)

#connect agents
CConnect(alice, bob, length=5.0)

#simulate agents
Simulation(alice, bob).run(verbose=True)

print(alice.master_clock.get_time())