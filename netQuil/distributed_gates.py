import sys
sys.path.insert(0, '/Users/matthewradzihovsky/documents/netQuil')
sys.path.insert(1, '/Users/matthewradzihovsky/documents/netQuil')

import numpy as np
import math
from pyquil.gates import *
from pyquil.parameters import Parameter, quil_exp
from pyquil.quilbase import DefGate

__all__ = ["QFT"]


def QFT(program, register):
    '''
    Performs Quantum Fourier Transform
    :param Program program: program for where to apply QFT
    :param List register: register of qubits to perform QFT on
    '''
       
    n = len(register)
    for i in range(n-1, -1, -1):
        program += H(register[i])
        for j in range(i-1, -1, -1):
            k = i-j+1
            program += CPHASE(2*np.pi/(2**k),register[j], register[i])


    return program
    