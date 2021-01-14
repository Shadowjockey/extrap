from ctypes import *
from typing import Sequence
from extrap.entities.measurement import Measurement
from extrap.modelers import single_parameter
from extrap.modelers.abstract_modeler import MultiParameterModeler as AbstractMultiParameterModeler
from extrap.modelers.abstract_modeler import SingularModeler
from extrap.modelers.modeler_options import modeler_options


class CPUMatrix(Structure):
    _fields_ = [('width', c_int), ('height', c_int), ('elements', POINTER(c_float))]

    def __repr__(self):
        repstring = "CPUMatrix\n width: "+str(self.width)+", height: "+str(self.height)
        return repstring


class CPUHypothesis(Structure):
    _fields_ = [('d', c_int),
                ('coefficients', c_float * 5),
                ('exponents', c_float * 10),
                ('smape', c_float),
                ('rss', c_float),
                ('combination', c_uint8 * 25)]

    def __repr__(self):
        rep_string = "-----------------------------------------------------------------\n"
        rep_string += f"Hypothesis (SMAPE = {self.smape:.4f}, RSS = {self.rss:.4f}\n"
        rep_string += " ".join(["Coefficients:", *[f"{c:.4f}" for c in self.coefficients[:self.d]]]) + "\n"
        exp = zip(self.exponents[:self.d*2:2], self.exponents[1:self.d*2:2])
        rep_string += " ".join(["Exponents:", *[f"({i:.2f},{j:.2f})" for i, j in exp]]) + "\n"
        rep_string += "Combination:" + "\n"
        for i in range(self.d):
            rep_string += " ".join([str(c) for c in self.combination[i*self.d:(i + 1) * self.d]]) + "\n"
        rep_string += "-----------------------------------------------------------------\n"
        return rep_string


@modeler_options
class GPUDirectMultiParameterModeler(AbstractMultiParameterModeler, SingularModeler):
    """
    This class represents the modeler for multi parameter functions.
    In order to create a model measurements at least 5 points are needed.
    The result is either a constant function or one based on the PMNF.
    """

    NAME = 'GPU-Direct-Multi-Parameter'
    single_parameter_modeler: 'SingleParameterModeler'
    use_crossvalidation = modeler_options.add(True, bool, 'Enables cross-validation', name='Cross-validation')
    allow_combinations_of_sums_and_products = modeler_options.add(True, bool,
                                                                  description="Allows models that consist of "
                                                                              "combinations of sums and products.")
    compare_with_RSS = modeler_options.add(False, bool,
                                           'If enabled the models are compared using their residual sum of squares '
                                           '(RSS) instead of their symmetric mean absolute percentage error (SMAPE)')

    def __init__(self):
        """
        Initialize SingleParameterModeler object.
        """
        super().__init__(use_median=False, single_parameter_modeler=single_parameter.Default())
        # value for the minimum number of measurement points required for modeling
        self.min_measurement_points = 5
        self.epsilon = 0.0005  # value for the minimum term contribution

    def create_model(self, measurements: Sequence[Measurement]):
        w = measurements[0].coordinate.dimensions + 1
        h = len(measurements)
        c_measurements = []
        for measurement in measurements:
            row = list(measurement.coordinate)
            row.append(measurement.mean if not self.use_median else measurement.median)
            c_measurements += row
        cu_mppm = CDLL('./lib/libcuMppm.so')
        float_arr = c_float * (h * w)
        elements = float_arr(*measurements)
        elements_ptr = cast(elements, POINTER(c_float))
        cu_mppm.find_hypothesis.restype = CPUHypothesis
        cpu_measurements = CPUMatrix(w, h, elements_ptr)
        hypothesis = cu_mppm.find_hypothesis(byref(cpu_measurements))
        print(hypothesis)
