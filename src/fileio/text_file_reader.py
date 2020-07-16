"""
This file is part of the Extra-P software (https://github.com/extra-p/extrap)

Copyright (c) 2020 Technical University of Darmstadt, Darmstadt, Germany

All rights reserved.
 
This software may be modified and distributed under the terms of
a BSD-style license. See the LICENSE file in the base
directory for details.
"""
import re
import logging
from entities.callpath import Callpath
from entities.coordinate import Coordinate
from entities.experiment import Experiment
from entities.measurement import Measurement
from entities.metric import Metric
from entities.parameter import Parameter
from fileio import io_helper
from fileio.io_helper import create_call_tree
from util.exceptions import FileFormatError

re_whitespace = re.compile(r'\s+')


def read_text_file(path, progress_event=lambda _: _):
    # read text file into list
    with open(path) as file:
        lines = file.readlines()

    # remove empty lines
    lines_no_space = [l for l in lines if not l.isspace()]

    # remove line breaks
    lines_no_space = [l.replace("\n", "") for l in lines_no_space]

    # create an experiment object to save the date loaded from the text file
    experiment = Experiment()

    # variables for parsing
    number_parameters = 0
    last_metric = None
    last_callpath = Callpath("")
    coordinate_id = 0

    if len(lines_no_space) == 0:
        raise FileFormatError(f'File contains no data: "{path}"')

    # parse text to extrap objects
    for i, line in enumerate(lines):
        progress_event(i / len(lines))
        if line.isspace() or line.startswith('#'):
            continue  # allow comments
        line = re_whitespace.sub(' ', line)
        # get field name
        field_separator_idx = line.find(" ")
        field_name = line[:field_separator_idx]
        field_value = line[field_separator_idx + 1:].strip()

        if field_name == "METRIC":
            # create a new metric if not already exists
            metric_name = field_value
            if experiment.metric_exists(metric_name) == False:
                metric = Metric(metric_name)
                experiment.add_metric(metric)
                last_metric = metric
            else:
                last_metric = metric
            # reset the coordinate id, since moving to a new region
            coordinate_id = 0

        elif field_name == "REGION":
            # create a new region if not already exists
            callpath_name = field_value

            callpath = Callpath(callpath_name)
            experiment.add_callpath(callpath)
            last_callpath = callpath

            # reset the coordinate id, since moving to a new region
            coordinate_id = 0

        elif field_name == "DATA":
            if last_metric is None:
                last_metric = Metric("")
            # create a new data set
            data_string = field_value
            data_list = data_string.split(" ")
            values = [float(d) for d in data_list]
            if number_parameters >= 1 and number_parameters <= 4:
                # create one measurement per repetition

                if coordinate_id >= len(experiment.coordinates):
                    raise FileFormatError(
                        f'To many DATA lines ({coordinate_id}) for the number of POINTS '
                        f'({len(experiment.coordinates)}) in line {i}.')
                measurement = Measurement(
                    experiment.coordinates[coordinate_id], last_callpath, last_metric, values)
                experiment.add_measurement(measurement)
                coordinate_id += 1
            elif number_parameters >= 5:
                raise FileFormatError("This input format supports a maximum of 4 parameters.")
            else:
                raise FileFormatError("This file has no parameters.")

        elif field_name == "PARAMETER":
            # create a new parameter
            parameters = field_value.split(' ')
            experiment.parameters += [Parameter(p) for p in parameters]
            number_parameters = len(experiment.parameters)

        elif field_name == "POINTS":
            coordinate_string = field_value.strip()
            if '(' in coordinate_string:
                coordinate_string = coordinate_string.replace(") (", ")(")
                coordinate_string = coordinate_string[1:-1]
                coordinate_strings = coordinate_string.split(')(')
            else:
                coordinate_strings = coordinate_string.split(' ')
            # create a new point
            if number_parameters == 1:
                parameter = experiment.parameters[0]
                coordinates = [Coordinate([(parameter, float(c))])
                               for c in coordinate_strings]
                experiment.coordinates.extend(coordinates)
            elif 1 < number_parameters < 5:
                for coordinate_string in coordinate_strings:
                    coordinate_string = coordinate_string.strip()
                    values = coordinate_string.split(" ")
                    coordinate = Coordinate(float(v) for v in values)
                    experiment.coordinates.append(coordinate)
            elif number_parameters >= 5:
                raise FileFormatError("This input format supports a maximum of 4 parameters.")
            else:
                raise FileFormatError("This file has no parameters.")
        else:
            raise FileFormatError(f'Encountered wrong field: "{field_name}" in line {i}: {line}')

    if last_metric == Metric(''):
        experiment.metrics.append(last_metric)
    if last_metric == Callpath(''):
        experiment.callpaths.append(last_callpath)
    # create the call tree and add it to the experiment
    callpaths = experiment.get_callpaths()
    call_tree = create_call_tree(callpaths)
    experiment.add_call_tree(call_tree)

    io_helper.validate_experiment(experiment)

    progress_event(None)
    return experiment
