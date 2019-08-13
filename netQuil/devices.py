import sys
sys.path.insert(0, '/Users/zacespinosa/Foundry/netQuil')
sys.path.insert(1, '/Users/matthewradzihovsky/documents/netQuil')

import numpy as np
import tqdm
import uuid

from pyquil import Program
from pyquil.gates import *
from netQuil import noise

__all__ = ["Fiber", "Laser", "Device"]

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
        return {delay: None, qubits: None}

    def get_results(self):
        '''
        Prints device information about trial to console. Should use tqdm.write in order to 
        avoid conflicts with network monitor. This function will only run when verbose 
        for the device is set to True.
        '''
        pass
    
    def reset(self): 
        '''
        reset is called between trials and resets all properties.
        ''' 
        pass 

class Fiber(Device):
    def __init__(self, length=0.0, attenuation_coefficient = -0.16, apply_error=True):
        '''
        Simulation of fiber optics with given length and attenuation coefficient. 

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
        :return: time qubits took to travel through fiber
        '''
        lost_qubits = []
        for i, qubit in enumerate(qubits):
            if qubit < 0: continue

            if self.apply_error:
                q = noise.measure(program, qubit, self.attenuation, "Fiber")
                if q is not None: 
                    lost_qubits.append(q)
                
        delay = self.length/signal_speed

        return {
            'delay': delay, 
            'lost_qubits': lost_qubits
        }

class Laser(Device):
    def __init__(self, pulse_length=10 * 10 ** -12, expected_photons=1.0, rotation_prob_variance=1.0, wavelength=1550, apply_error=True):
        '''
        Simulation of laser at 1550nm wavelength. Laser produce photons according to poisson
        distribution, centered around expected_photons. 
        '''
        self.variance = rotation_prob_variance
        self.wavelength = wavelength
        self.photon_expectation = expected_photons
        self.pulse_length = pulse_length
        self.apply_error = apply_error
        self.name = 'Laser'
        self.success = 0
        self.trials = 0
        
    def apply(self, program, qubits):
        '''
        Applies laser effect to qubits
        :param Program program: global program
        :param List<int> qubits: list of qubits going through laser
        :return: time it took qubits to pass through device
        '''
        for qubit in qubits:
            if qubit < 0: continue

            if self.apply_error:
                numPhotons = np.random.poisson(lam=self.photon_expectation)
                self.trials += len(qubits)
                if numPhotons == self.photon_expectation: self.success += 1
                '''
                Rotation Noise
                noise.normal_unitary_rotation(program, qubit, 0.5, self.variance)
                '''
        delay = self.pulse_length
        return {
            'delay': delay
        }

    def get_results(self):
        try: 
            tqdm.tqdm.write('{} has a signal to noise ratio of {}/{}'.format(self.name, self.success, self.trials))
        except:
            pass

    def reset(self):  
        self.success = 0
        self.trials = 0 
