# Remove in future: currently allows us to import netQuil
import sys
sys.path.insert(0, '/Users/zacespinosa/Foundry/netQuil')
sys.path.insert(1, '/Users/matthewradzihovsky/documents/netQuil')

import numpy as np

from pyquil import Program
from pyquil.api import WavefunctionSimulator, QVMConnection
from pyquil.gates import *
from netQuil import *

####################################################
# TRIALS, CUSTOM AND DEFAULT DEVICES, AND VERBOSE
####################################################
class Simple_Fiber(Device): 
    def __init__(self, length, fiber_quality, rotation_std):
       self.fiber_quality = fiber_quality
       self.length = length
       self.rotation_std = rotation_std
       self.signal_speed = 2.998 * 10 ** 5 #speed of light in km/s

    def apply(self, program, qubits):
        for qubit in qubits: 
            # Apply noise
            if np.random.rand() > self.fiber_quality:
                rotation_angle = np.random.normal(0, self.rotation_std)
                program += RX(rotation_angle, qubit)

        delay = self.length/self.signal_speed

        return {
            'delay': delay,
        }

class Alice(Agent):
    def run(self):
        p = self.program
        for q in self.qubits:
            p += H(q)
            p += X(q)
            self. qsend('Bob', [q])

class Bob(Agent):
    def run(self):
        p = self.program
        for _ in range(3): 
            q = self.qrecv(alice.name)[0]
            # If qubit is not lost
            if q >= 0: 
                p += MEASURE(q, ro[q])

p = Program()
ro = p.declare('ro', 'BIT', 3)

alice = Alice(p, qubits=[0,1,2])
bob = Bob(p)

# Define source device
laser = Laser(rotation_prob_variance=.9) 
alice.add_source_devices([laser])

# Define transit devices and connection
custom_fiber = Simple_Fiber(length=5, fiber_quality=.6, rotation_std=5)
fiber = Fiber(length=5, attenuation_coefficient=-.20) 
QConnect(alice, bob, transit_devices=[fiber, custom_fiber])

# Run simulation
programs = Simulation(alice, bob).run(trials=10, agent_classes=[Alice, Bob]) 

# Run programs
qvm = QVMConnection()
for idx, program in enumerate(programs): 
    results = qvm.run(program)
    print('Program {}: '.format(idx), results)
