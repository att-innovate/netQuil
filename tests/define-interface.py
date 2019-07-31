from netQuil import *
from pyquil import Program
from pyquil.gates import *
from pyquil.api import WavefunctionSimulator

class Alice(Agent): 
    def __init__(self): 
        self.add_device('source', Laser(1550))
        self.add_device('source', IntensityMagnifier(darkNoise = 20))
        self.add_device('source', PhaseMagnifier(error = 30))

        self.add_device('target', Splitter(darkNoise = 20))
        self.add_device('target', Splitter(darkNoise = 20))

    def distribute_bell_pair(self, target, p): 
        '''
            Note: two options for preventing manipulation of inaccessible qbits
            1. Add access list to self/target in create_qpacket
            2. Add access list to self/target in channel
        '''
        # Create packet stores shallow copy of program on bob and alice,
        # along with accessible indices
        source_qubits = [0, 1]
        target_qubits = [0]
        packet = create_qpacket(source_qubits, target_qubits, p)
        return alice.qsend(target, packet) 

    def teleport(self, target, p):
        # Perform teleportation
        p += CNOT(2,0)
        p += H(2)
        # Measure Qbits
        ro = p.declare('ro', 'BIT', 2)
        apply_x = MEASURE (0, ro[0])
        apply_z = MEASURE (2, ro[1])
        # Send Cbits
        bits = [apply_x, apply_z]
        alice.csend(self, bob, bits)

    def run():
        # Create bell pair and send half to Bob 
        p = Program(H(0), CNOT(0,1))
        distribute_bell_pair(self, target, p)
        teleport(self, target, p)
        self.close()

class Bob(Agent): 
    def __init__(self): 
        self.add_device('source', Laser(1550))
        self.add_device('source', IntensityMagnifier(darkNoise = 20))
        self.add_device('source', PhaseMagnifier(error = 30))

        self.add_device('target', Splitter(darkNoise = 20))
        self.add_device('target', Splitter(darkNoise = 20))

    def run(self, target): 
        # Bob receives a qubit from Alice
        qubits = self.qrecv(alice)
        # Bob receives classical instructions
        apply_x, apply_z = self.crecv()
        if apply_x: self.p += X(1)
        if apply_z: self.p += Z(1)
        # Measure the output
        self.close()
        
bob = Bob(program, [0,1])
alice = Alice(program, [2])
        
''' 
    Could extend the QConnect and CConnect classes to take Channel objects 
    defining a combination of FiberOptics and FreeSpace connections 
'''
devices = [FiberOptics(), FreeSpace(), FiberOptics()]
QConnect(bob, alice, devices)
Simulate(bob, alice).run()




''' 
    Notes to Self: 
        - Find better way to represent nodes .add_device and.add_device data)
        - Look into simultaneous.add_device and.add_device - agents are threads
          multi-processing. Both.add_device and.add_device!
        - Consider creating protocol class 
        - Explore need for createPacket
'''