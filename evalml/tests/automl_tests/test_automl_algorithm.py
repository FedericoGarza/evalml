import pytest

from evalml.automl.automl_algorithm import AutoMLAlgorithm


def test_automl_algorithm_init_base():
    with pytest.raises(TypeError, match="Can't instantiate abstract class AutoMLAlgorithm with abstract methods next_batch"):
        AutoMLAlgorithm()


class DummyAlgorithm(AutoMLAlgorithm):
    def __init__(self, dummy_pipelines=None):
        super().__init__()
        self._dummy_pipelines = dummy_pipelines or []

    def next_batch(self):
        self._pipeline_number += 1
        self._batch_number += 1
        if len(self._dummy_pipelines) > 0:
            return self._dummy_pipelines.pop()
        raise StopIteration('No more pipelines!')


def test_automl_algorithm_dummy():
    algo = DummyAlgorithm()
    assert algo.pipeline_number == 0
    assert algo.batch_number == 0

    algo = DummyAlgorithm(dummy_pipelines=['pipeline 3', 'pipeline 2', 'pipeline 1'])
    assert algo.pipeline_number == 0
    assert algo.batch_number == 0
    assert algo.next_batch() == 'pipeline 1'
    assert algo.pipeline_number == 1
    assert algo.batch_number == 1
    assert algo.next_batch() == 'pipeline 2'
    assert algo.pipeline_number == 2
    assert algo.batch_number == 2
    assert algo.next_batch() == 'pipeline 3'
    assert algo.pipeline_number == 3
    assert algo.batch_number == 3
    with pytest.raises(StopIteration, match='No more pipelines!'):
        algo.next_batch()


def test_automl_algorithm_deprecation_warning():
    class UsePipelineMaxAlgo(AutoMLAlgorithm):
        def __init__(self):
            super().__init__(max_pipelines=5)

        def next_batch(self):
            pass

    with pytest.warns(DeprecationWarning, match="`max_pipelines will be deprecated in the next release. Use `max_iterations` instead."):
        UsePipelineMaxAlgo()
