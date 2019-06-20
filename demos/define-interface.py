from qnetdes import *
from pyquil import Program

class Alice(Agent): 
    def __init__(self): 
        self.sending.push(Sources.laser(lambda = 1550))
        self.sending.push(IntensityMagnifier(darkNoise = 20))
        self.sending.push(PhaseMagnifier(error = 30))

        self.receiving.push(Receiver.splitter(darkNoise = 20))
        self.receiving.push(Receiver.splitter(darkNoise = 20))

    def entanglementProtocol(): 
        p = Program(H(0), CNOT(0,1))
        return p

    def send(self, target, program): 
        ''' 
            This is optional and may over complicate for now but 
            eventually could add things like program name and meta data
        '''
        packet = createPacket(program) 
        try: 
            qsend(self, target, packet) 
        catch: 
            print('Error sending: ', packet)
    
    def receive(self):
        for _ in qstream: 
            qrecv()

class Bob(Agent): 
    def __init__(self): 
        self.sending.push(Sources.laser(lambda = 1750))
        self.sending.push(IntensityMagnifier(darkNoise = 20))

        self.receiving.push(Reciever.splitter(darkNoise = 20))
        self.receiving.push(Reciever.splitter(darkNoise = 20))

    def run(self, target): 
        # start receiving protocol
        for _ in qstream:
            p = qrecv(self, target, p) 

bob = Bob()
alice = Alice()
''' 
    Could extend the QConnect and CConnect classes to take Channel objects 
    defining a combination of FiberOptics and FreeSpace connections 
'''
QConnect(bob, alice, FiberOptics)
CConnect(bob, alice, FreeSpace)
Simulate(bob, alice).run()

''' 
    Note to Self: 
        - Find better way to represent nodes (receiving and sending data)
        - Look into simultaneous sending and receiving - agents are threads
          multi-processing. Both sending and receiving!
        - Consider creating protocol class 
        - Explore need for createPacket
'''