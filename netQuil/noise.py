import sys
sys.path.insert(1, '/Users/matthewradzihovsky/documents/netQuil')
sys.path.insert(0, '/Users/zacespinosa/Foundry/netQuil')

import numpy as np
import uuid

from pyquil.gates import *
from pyquil.quil import DefGate
from pyquil.noise import pauli_kraus_map

__all__ = ["bit_flip", "phase_flip", "depolarizing_noise", "measure","normal_unitary_rotation"]

ro = None

def kraus_op_bit_flip(prob: float):
    noisy_I = np.sqrt(1-prob) * np.asarray([[1, 0], [0, 1]])
    noisy_X = np.sqrt(prob) * np.asarray([[0, 1], [1, 0]])
    return [noisy_I, noisy_X]


def kraus_op_phase_flip(prob: float):
    noisy_I = np.sqrt(1-prob) * np.asarray([[1, 0], [0, 1]])
    noisy_Z = np.sqrt(prob) * np.asarray([[1, 0], [0, -1]])
    return [noisy_I, noisy_Z]


def kraus_op_depolarizing_channel(prob: float):
    noisy_I = np.sqrt(1-prob) * np.asarray([[1, 0], [0, 1]])
    noisy_X = np.sqrt(prob/3) * np.asarray([[0, 1], [1, 0]])
    noisy_Z = np.sqrt(prob/3) * np.asarray([[1, 0], [0, -1]])
    noisy_Y = np.sqrt(prob/3) * np.asarray([[0, 0-1.0j], [0+1.0j, 0]])
    return [noisy_I, noisy_X, noisy_Y, noisy_Z]

def random_unitary(n):
    # draw complex matrix from Ginibre ensemble
    z = np.random.randn(n, n) + 1j * np.random.randn(n, n)
    # QR decompose this complex matrix
    q, r = np.linalg.qr(z)
    # make this decomposition unique
    d = np.diagonal(r)
    l = np.diag(d) / np.abs(d)
    return np.matmul(q, l)



def bit_flip(program, qubit, prob: float):
    '''
    Apply a bit flip with probability 

    :param Program program: program to apply noise to
    :param Integer qubit: qubit to apply noise to 
    :param Float prob: probability of apply noise 
    '''
    unique_id = uuid.uuid1().int

    flip_noisy_I_definition = DefGate("flipNOISE" + str(unique_id), random_unitary(2))
    program += flip_noisy_I_definition
    
    program.define_noisy_gate("flipNOISE" + str(unique_id), [qubit], kraus_op_bit_flip(prob))
    program += ("flipNOISE" + str(unique_id), qubit)

def phase_flip(program, qubit, prob: float):
    '''
    Apply a phase flip with probability

    :param Program program: program to apply noise to
    :param Integer qubit: qubit to apply noise to 
    :param Float prob: probability of apply noise 
    '''

    unique_id = uuid.uuid1().int

    phase_noisy_I_definition = DefGate("phaseNOISE" + str(unique_id), random_unitary(2))
    program += phase_noisy_I_definition
    
    program.define_noisy_gate("phaseNOISE" + str(unique_id), [qubit], kraus_op_phase_flip(prob))
    program += ("phaseNOISE" + str(unique_id), qubit)

def depolarizing_noise(program, qubit, prob: float):
    '''
    Apply depolarizing noise with probability

    :param Program program: program to apply noise to
    :param Integer qubit: qubit to apply noise to 
    :param Float prob: probability of apply noise 
    '''
    unique_id = uuid.uuid1().int

    dp_noisy_I_definition = DefGate("dpNOISE" + str(unique_id), random_unitary(2))
    program += dp_noisy_I_definition
    
    program.define_noisy_gate("dpNOISE" + str(unique_id), [qubit], kraus_op_depolarizing_channel(prob))
    program += ("dpNOISE" + str(unique_id), qubit)

def measure(program, qubit, prob: float, name):
    '''
    Measure the qubit with probability

    :param Program program: program to apply noise to
    :param Integer qubit: qubit to apply noise to 
    :param Float prob: probability of apply noise 
    :param String name: name of quil classical register to measure to.
    :returns: None if qubit is not measured and qubit if qubit is measured
    '''
    if np.random.rand()> prob:
        global ro

        devices_ro_exists = False
        ro_exists = False
        for inst in program.instructions: 
            try: 
                if inst.name == name:
                    devices_ro_exists = True
                elif inst.name == "ro":
                    ro_exists = True
            except: pass

        if not ro_exists:
            ro = program.declare("ro", 'BIT', 1)
        elif ro_exists and not devices_ro_exists:
            ro = program.declare(name, 'BIT', 1)

        program += MEASURE(qubit, ro)
        return qubit
    return None

def normal_unitary_rotation(program, qubit, prob:float, variance):
    '''
    Apply X and Z rotation with probability

    :param Program program: program to apply noise to
    :param Integer qubit: qubit to apply noise to 
    :param Float prob: probability of apply noise 
    :param Float variance: variance of rotation angle
    '''
    if np.random.rand() > prob:
        x_angle, z_angle = np.random.normal(0, variance, 2)
        program += RX(x_angle, qubit)
        program += RZ(z_angle, qubit)
    