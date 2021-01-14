from extrap.entities.callpath import Callpath
from extrap.entities.metric import Metric
from extrap.entities.terms import *
from extrap.entities.hypotheses import *
from extrap.modelers.multi_parameter.gpu_direct_multi_parameter_modeler import GPUDirectMultiParameterModeler
from extrap.modelers.multi_parameter.multi_parameter_modeler import MultiParameterModeler
from extrap.fileio import text_file_reader


def hypothesis_to_cpp(hypothesis: MultiParameterHypothesis, dimension):
    func = hypothesis.function
    coefficients = [func.constant_coefficient]
    ctps = [["0", "0"] for i in range(dimension)]
    combination = [[0] * dimension for i in range(dimension)]
    for i, compound_term in enumerate(func.compound_terms):
        compound_term: MultiParameterTerm
        coefficients.append(compound_term.coefficient)
        for param_index, parameter_term in compound_term.parameter_term_pairs:
            combination[i][param_index] = 1
            parameter_term: CompoundTerm
            for simple_term in parameter_term.simple_terms:
                inner_index = 0 if simple_term.term_type == "polynomial" else 1
                string = str(simple_term.exponent)
                string = string.replace("/", "./")
                ctps[param_index][inner_index] = string

    coefficients += [0] * (dimension - len(coefficients))
    print("float coefs[] = {" + ",".join(str(coef) for coef in coefficients) + "};")
    print("float ctps[] = {" + ",".join(",".join(ctp) for ctp in ctps) + "};")
    print("unsigned char combination[] = {" + ",".join(",".join(str(c) for c in comb) for comb in combination) + "};")


def main():
    experiment = text_file_reader.read_text_file("tests/data/text/two_parameter_1.txt")
    modeller = GPUDirectMultiParameterModeler()
    model = modeller.create_model(experiment.measurements[(Callpath('reg'), Metric('metr'))])


if __name__ == '__main__':
    main()
