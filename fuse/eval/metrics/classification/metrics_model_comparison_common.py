
"""
(C) Copyright 2021 IBM Corp.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Created on June 30, 2021

"""

from typing import Any, Callable, Dict, Optional, Sequence, Tuple, Union

import numpy as np

from fuse.eval.metrics.metrics_common import MetricWithCollectorBase
from .metrics_classification_common import MetricMultiClassDefault
from fuse.eval.metrics.libs.model_comparison import ModelComparison
from fuse.eval.metrics.metrics_common import MetricDefault

class MetricDelongsTest(MetricMultiClassDefault):
    def __init__(self, pred1: str, pred2: str, target: str, class_names: Optional[Sequence[str]] = None, **kwargs):
        # :param pred1: key name for the predictions of model 1
        # :param pred2: key name for the predictions of model 2
        # :param target: key name for the ground truth labels
        # :param class_names: class names. required for multi-class classifiers

        super().__init__(pred=None, target=target, metric_func=ModelComparison.delong_auc_test, \
                         class_names=class_names, pred1=pred1, pred2=pred2, **kwargs)

class MetricContingencyTable(MetricDefault):
    def __init__(self, var1: str, var2: str, **kwargs):
        """
        Create contingency table from two paired variables.
        :param var1: key name for the first variable
        :param var2: key name for the second variable
        """
        super().__init__(pred=None, target=None, metric_func=ModelComparison.contingency_table, \
                            var1=var1, var2=var2, **kwargs)


class MetricMcnemarsTest(MetricMultiClassDefault):
    def __init__(self, contingency_table: str, **kwargs):
        """
        McNemar's statistical test for comparing two paired nominal data in the sense 
        of the statistics of their disagreements, as seen in the contingency table.
        :param contingency_table: key name for the contingency table
        """
        super().__init__(pred=None, target=None, metric_func=ModelComparison.mcnemars_test, \
                           contingency_table=contingency_table, **kwargs)
