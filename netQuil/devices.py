import sys
sys.path.insert(0, '/Users/matthewradzihovsky/documents/netQuil')
sys.path.insert(1, '/Users/matthewradzihovsky/documents/netQuil')

import numpy as np
import uuid

from pyquil import Program
from pyquil.gates import *
from netQuil import noise

__all__ = ["Fiber", "Laser", "SNSPD", "Intensity_Modulator"]

signal_speed = 2.998 * 10 ** 5 #speed of light in km/s
class Device(): 
    '''
    Base class for all source and target devices
    '''
    def __init__(self): 
        self.name = 'Device'
        self.success = 0
        self.trials = 0
    
    def apply(self, program, qubits):
        '''
        This function should be overwritten by children classes, and 
        should include runtime code defining how child devices impact qubits

        :param Pyquil<Program> program: program to manipulate
        :param List qubits: list of qubits passing through device
        '''
        pass

    def get_success(self):
        try: 
            print('{} has a signal to noise ratio of {}/{}'.format(self.name, self.success, self.trials))
        except:
            pass
    
    def reset(self): 
        self.success = 0
        self.trials = 0 

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
            if self.apply_error:
                noise.measure(program, qubit, self.attenuation, "Fiber")
        delay = self.length/signal_speed
        return delay


class Laser(Device):
    def __init__(self, pulse_length=10 * 10 ** -12, expected_photons=1.0, rotation_prob_variance=1.0, wavelength=1550, apply_error=True):
        self.variance = rotation_prob_variance
        self.wavelength = wavelength
        self.photon_expectation = expected_photons
        self.pulse_length = pulse_length
        self.apply_error = apply_error
        self.name = 'Laser'
        self.success = 0
        self.trials = 0
        
    def apply(self, program, qubits):
        for qubit in qubits:
            if self.apply_error:
                numPhotons = np.random.poisson(lam=self.photon_expectation)
                self.trials += len(qubits)
                if numPhotons == self.photon_expectation: self.success += 1
                '''
                Rotation Noise
                noise.normal_unitary_rotation(program, qubit, 0.5, self.variance)
                '''
        delay = self.pulse_length
        return delay


class SNSPD(Device):
    def __init__(self,  apply_error=True):
        pass

    def apply(self, program, qubits):
        pass


class Intensity_Modulator(Device):
    def __init__(self, apply_error=True, Average_Photons=1.0):
        pass

        
    def apply(self, program, qubits):
        pass





        

    