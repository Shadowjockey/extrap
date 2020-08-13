from typing import Optional, List

import numpy
from marshmallow import fields

from entities.callpath import CallpathSchema
from entities.hypotheses import Hypothesis, HypothesisSchema
from entities.measurement import Measurement
from entities.metric import MetricSchema
from util.caching import cached_property
from util.deprecation import deprecated
from util.serialization_schema import Schema


class Model:

    def __init__(self, hypothesis, callpath=None, metric=None):
        self.hypothesis: Hypothesis = hypothesis
        self.callpath = callpath
        self.metric = metric
        self.measurements: Optional[List[Measurement]] = None

    @deprecated("Use property directly.")
    def get_hypothesis(self):
        return self.hypothesis

    @deprecated("Use property directly.")
    def get_callpath_id(self):
        return self.callpath.id

    @deprecated("Use property directly.")
    def get_metric_id(self):
        return self.metric.id

    @cached_property
    def predictions(self):
        coordinates = numpy.array([m.coordinate for m in self.measurements])
        return self.hypothesis.function.evaluate(coordinates.transpose())

    def __eq__(self, other):
        if not isinstance(other, Model):
            return NotImplemented
        elif self is other:
            return True
        else:
            return self.callpath == other.callpath and \
                   self.metric == other.metric and \
                   self.hypothesis == other.hypothesis and \
                   self.measurements == other.measurements


class ModelSchema(Schema):
    def create_object(self):
        return Model(None)

    hypothesis = fields.Nested(HypothesisSchema)
    callpath = fields.Nested(CallpathSchema)
    metric = fields.Nested(MetricSchema)
