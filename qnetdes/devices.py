import sys
sys.path.insert(0, '/Users/matthewradzihovsky/documents/qnetdes')
sys.path.insert(1, '/Users/matthewradzihovsky/documents/qnetdes')

import numpy as np
import uuid

from pyquil import Program
from pyquil.gates import *
from qnetdes import *

__all__ = ["Fiber", "Laser", "SNSPD", "Intensity_Modulator"]

signal_speed = 2.998 * 10 ** 5 #speed of light in km/s
class Device(): 
    def __init__(self): 
        pass
    
    def apply(self, program, qubits):
        pass

class Fiber(Device):
    def __init__(self, length=0.0, attenuation_coefficient = -0.16, apply_error=True):
        '''
        :param Float length: length of fiber optical cable in km
        :param Float attenuation_coefficient: coefficient determining likelihood of photon loss
        :param Boolean apply_error: True is device should apply error, otherwise, only returns time delay
        '''
        decibel_loss = length*attenuation_coefficient
        self.attenuation = 10 ** (decibel_loss / 10)
        self.apply_error = apply_error
        self.length = length

        
    def apply(self, program, qubits):
        '''
        Applies device's error and returns time that photon took to pass through simulated device

        :param Program program: program to be modified
        :param List qubits: qubits being sent
        '''
        for qubit in qubits:
            if np.random.rand() < self.attenuation and qubit is not None and self.apply_error:
                print('Apply Fiber Error')
                ro = program.declare('fiber' + str(uuid.uuid1().int), 'BIT', 1)
                program += MEASURE(qubit, ro) 
        delay = self.length/signal_speed
        return delay


class Laser(Device):
    def __init__(self, pulse_length=10 * 10 ** -12, expected_photons=1.0, rotation_prob_variance=1.0, wavelength=1550, apply_error=True):
        self.variance = rotation_prob_variance
        self.wavelength = wavelength
        self.photon_expectation = expected_photons
        self.pulse_length = pulse_length
        self.apply_error = apply_error
        
    def apply(self, program, qubits):
        for qubit in qubits:
            if qubit is not None and self.apply_error:
                numPhotons = np.random.poisson(lam=self.photon_expectation)
                print("Produced ", numPhotons, " photons")
                x_angle, z_angle = np.random.normal(0,self.variance,2)
                program += RX(x_angle, qubit)
                program += RZ(z_angle, qubit)
        delay = self.pulse_length
        return delay


class SNSPD(Device):
    def __init__(self,  expectation_photons=1, apply_error=True):
        self.expected = expectation_photons
        self.apply_error = apply_error

    def apply(self, program, qubits):
        for qubit in qubits:
            if qubit is not None and self.apply_error:
                ro = program.declare('SNSPD' + str(uuid.uuid1().int), 'BIT', 1)
                program += MEASURE(qubit, ro) 
        delay = self.length
        return delay


class Intensity_Modulator(Device):
    def __init__(self, Average_Photons=1.0, apply_error=True):

        decibel_loss = length*attenuation_coefficient
        self.attenuation = 10 ** (decibel_loss / 10)
        self.apply_error = apply_error
        self.length = length

        
    def apply(self, program, qubits):
        return delay





        

    