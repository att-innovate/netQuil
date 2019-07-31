import matplotlib.image as image
import matplotlib.pyplot as plt
import numpy as np
import sys
sys.path.insert(1, '/Users/matthewradzihovsky/documents/netQuil')
sys.path.insert(0, '/Users/zacespinosa/Foundry/netQuil')

import pyquil.api as api
from pyquil import Program
from pyquil.api import WavefunctionSimulator, QVMConnection
from pyquil.gates import *
from netQuil import *

class Charlie(Agent):
    '''
    Charlie sends Bell pairs to Alice and Bob
    '''
    def run(self):
        p = self.program
        for i in range(0,len(alice.cmem),2):
            p += H(i)
            #print("charlie has qubits", charlie.qubits)
            p += CNOT(i, i+1)
            self.qsend(alice.name, [i])
            self.qsend(bob.name, [i+1])
        
    
class Alice(Agent):
    '''
    Alice sends Bob superdense-encoded classical bits, intercepted by Eve
    '''
    def run(self):
        p = self.program
        for i in range(0,len(self.cmem),2):
            bit1 = self.cmem[i]
            bit2 = self.cmem[i+1]
            qubitsCharlie = self.qrecv(charlie.name)
            a = qubitsCharlie[0]

            if bit2 == 1: p += X(a)
            if bit1 == 1: p += Z(a)
            
            self.qsend(eve.name, [a])

class Bob(Agent):
    '''
    Bob reconstructs Alice's classical bits
    '''
    def run(self):
        p = self.program
        #ro = p.declare('ro', 'BIT', len(alice.cmem))
        for i in range(0,len(alice.cmem),2):
            qubitsAlice = self.qrecv(eve.name)
            qubitsCharlie = self.qrecv(charlie.name)
            a = qubitsAlice[0]
            c = qubitsCharlie[0]
            p += CNOT(a,c)
            p += H(a)
            p += MEASURE(a, ro[i])
            p += MEASURE(c, ro[i+1])


class Eve(Agent):
    '''
    #Eve intercepts message from Alice, measures, and sends to Bob
    '''
    def run(self):
        p = self.program
        #ro = p.declare('roEve', 'BIT', len(alice.cmem))
        for i in range(0,len(alice.cmem),2):
            qubitsAlice = self.qrecv(alice.name)
            a = qubitsAlice[0]
            p += MEASURE(a, ro[i+len(alice.cmem)])
            self.qsend(bob.name, [a])



def plot_alice_bob_eve_images(eve_bits, bob_bits,img):
    eve_img = np.reshape(np.packbits(eve_bits), (int(img.shape[0]/2), img.shape[1], img.shape[2]))
    bob_img = np.reshape(np.packbits(bob_bits), img.shape)
    f, ax = plt.subplots(1, 3, figsize = (18, 9))
    ax[0].imshow(img)
    ax[0].axis('off')
    ax[0].title.set_text("Alice's image")
    ax[1].imshow(eve_img)
    ax[1].axis('off')
    ax[1].title.set_text("Eve's image")
    ax[2].imshow(bob_img)
    ax[2].axis('off')
    ax[2].title.set_text("Bob's image")
    plt.tight_layout()
    plt.show()

def pltImage(img_bits, img):
    img_bits = np.reshape(np.packbits(img_bits), img.shape)
    f, ax = plt.subplots(1, 3, figsize = (18, 9))
    ax[0].imshow(img)
    ax[0].axis('off')
    plt.tight_layout()
    plt.show()

        
img = image.imread("./Images/mochi11.jpg")
print(img.shape)
img_bits = list(np.unpackbits(img))
pltImage(img_bits, img)
print("LEN IMG_BITS TOTAL", len(img_bits))
#img_bits = img_bits[0:20]

start = 0
end = 20

qvm = QVMConnection()
resultsEve = []
resultsBob = []
i = 0
print("LEN IMG_BITS TOTAL", len(img_bits))

while end <= len(img_bits):
    curImg_bits = img_bits[start:end]
    qubitsUsed = list(range(len(curImg_bits)))

    print("START", start)
    print("END", end)
    program = Program()
    ro = program.declare('ro', 'BIT', 2*len(curImg_bits))

    #define agents
    alice = Alice(program, cmem=curImg_bits)
    bob = Bob(program)
    charlie = Charlie(program, qubits=qubitsUsed)
    eve = Eve(program)

    #connect agents
    QConnect(alice, bob)
    QConnect(bob, charlie)
    QConnect(alice, charlie)
    QConnect(alice, eve)
    QConnect(bob, eve)


    #simulate agents
    Simulation(alice,charlie,bob,eve).run(trials=1, agent_classes=[Alice, Charlie, Bob, Eve])
    results = qvm.run(program)

    resultsBob.extend(results[0][0:len(curImg_bits)])
    resultsEve.extend(results[0][len(curImg_bits):])

    start = end
    if end == len(img_bits):
        break
    elif len(img_bits) >= end+20:
        end += 20
    else:
        end = len(img_bits)
    i += 1
    print("simulated: ", i)
        

plot_alice_bob_eve_images(resultsEve, resultsBob, img)

wf_sim = WavefunctionSimulator()
resultWF = wf_sim.wavefunction(program)


#print(program)


#print('Final state: ', resultWF)
print('Alice\'s bits: ', img_bits)
print('Bob\'s results:', resultsBob)
print(len(resultsBob))
print('Eve\'s stolen results:', resultsEve)


print('Bob\'s time:', bob.time)
print('Alice\'s time:', alice.time)
print('Eve\'s time:', eve.time)
print('Charlie\'s time:', charlie.time)
print('DIFFERENCE:', list(set(resultsBob) - set(img_bits)))



