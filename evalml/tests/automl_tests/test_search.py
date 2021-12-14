from unittest.mock import patch

import pandas as pd
import pytest

from evalml.automl import AutoMLSearch, search
from evalml.automl.automl_algorithm import DefaultAlgorithm
from evalml.objectives import LogLossBinary
from evalml.utils import infer_feature_types


@patch("evalml.data_checks.default_data_checks.DefaultDataChecks.validate")
@patch("evalml.automl.AutoMLSearch.search")
def test_search(mock_automl_search, mock_data_checks_validate, X_y_binary):
    X, y = X_y_binary
    # this doesn't exactly match the data check results schema but its enough to trigger the error in search()
    data_check_results_expected = {"warnings": ["Warning 1", "Warning 2"]}
    mock_data_checks_validate.return_value = data_check_results_expected
    automl, data_check_results = search(X_train=X, y_train=y, problem_type="binary")
    assert isinstance(automl, AutoMLSearch)
    assert data_check_results is data_check_results_expected
    mock_data_checks_validate.assert_called_once()
    data, target = (
        mock_data_checks_validate.call_args[0][0],
        mock_data_checks_validate.call_args[1]["y"],
    )
    pd.testing.assert_frame_equal(data, infer_feature_types(X))
    pd.testing.assert_series_equal(target, infer_feature_types(y))
    mock_automl_search.assert_called_once()


@patch("evalml.data_checks.default_data_checks.DefaultDataChecks.validate")
@patch("evalml.automl.AutoMLSearch.search")
def test_search_data_check_error(
    mock_automl_search, mock_data_checks_validate, X_y_binary
):
    X, y = X_y_binary
    # this doesn't exactly match the data check results schema but its enough to trigger the error in search()
    data_check_results_expected = {"errors": ["Error 1", "Error 2"]}
    mock_data_checks_validate.return_value = data_check_results_expected
    automl, data_check_results = search(X_train=X, y_train=y, problem_type="binary")
    assert automl is None
    assert data_check_results == data_check_results_expected
    mock_data_checks_validate.assert_called_once()
    data, target = (
        mock_data_checks_validate.call_args[0][0],
        mock_data_checks_validate.call_args[1]["y"],
    )
    pd.testing.assert_frame_equal(data, infer_feature_types(X))
    pd.testing.assert_series_equal(target, infer_feature_types(y))


@patch("evalml.data_checks.ts_splitting_data_check.TimeSeriesSplittingDataCheck")
def test_n_splits_passed_to_ts_splitting_data_check(mock_ts_splitting_dc, ts_data):
    from pprint import pprint
    X = pd.DataFrame(pd.date_range("1/1/21", periods=100), columns=["date"])
    y = pd.Series(0 if i < 40 else 1 for i in range(100))

    problem_config = {"gap": 1, "max_delay": 1, "forecast_horizon": 1, "time_index": "date"}

    mock_ts_splitting_dc.n_splits.return_value = 6
    print(mock_ts_splitting_dc.n_splits.return_value)
    # Set n_splits to 4 to verify it gets passed to the Time Series Splitting Data Check
    _, data_checks = search(X_train=X, y_train=y, problem_configuration=problem_config, problem_type="time series binary", n_splits=4)
    pprint(data_checks)
    #mock_ts_splitting_dc.assert_called_with("time series binary", 4)
    #assert len(data_checks["errors"][0]['details']['invalid_splits']) == 4


@pytest.mark.parametrize(
    "problem_config", [None, "missing_time_index", "has_time_index"]
)
def test_search_data_check_error_timeseries(problem_config):
    X, y = pd.DataFrame({"features": range(30)}), pd.Series(range(30))
    problem_configuration = None

    dates = pd.date_range("2021-01-01", periods=29).append(
        pd.date_range("2021-01-31", periods=1)
    )
    X["dates"] = dates

    if problem_config == "missing_time_index":
        problem_configuration = {"gap": 4}
        with pytest.raises(
            ValueError,
            match="time_index has to be passed in problem_configuration.",
        ):
            search(
                X_train=X,
                y_train=y,
                problem_type="time series regression",
                problem_configuration=problem_configuration,
            )
    elif not problem_config:
        with pytest.raises(
            ValueError,
            match="the problem_configuration parameter must be specified.",
        ):
            search(
                X_train=X,
                y_train=y,
                problem_type="time series regression",
                problem_configuration=problem_configuration,
            )
    else:
        problem_configuration = {"time_index": "dates"}
        automl, data_check_results = search(
            X_train=X,
            y_train=y,
            problem_type="time series regression",
            problem_configuration=problem_configuration,
        )
        assert len(data_check_results["warnings"]) == 1
        assert len(data_check_results["errors"]) == 1


@patch("evalml.data_checks.default_data_checks.DefaultDataChecks.validate")
@patch("evalml.automl.AutoMLSearch.search")
def test_search_args(mock_automl_search, mock_data_checks_validate, X_y_binary):
    X, y = X_y_binary
    automl, _ = search(
        X_train=X,
        y_train=y,
        problem_type="binary",
        max_time=42,
        patience=3,
        tolerance=0.5,
        mode="fast",
    )
    assert automl.max_time == 42
    assert automl.patience == 3
    assert automl.tolerance == 0.5
    assert automl.max_batches == 4
    assert isinstance(automl._automl_algorithm, DefaultAlgorithm)

    automl, _ = search(
        X_train=X,
        y_train=y,
        problem_type="binary",
        max_time=42,
        patience=3,
        tolerance=0.5,
        mode="long",
    )
    assert automl.max_time == 42
    assert automl.patience == 3
    assert automl.tolerance == 0.5
    assert automl.max_batches == 999
    assert isinstance(automl._automl_algorithm, DefaultAlgorithm)

    automl, _ = search(
        X_train=X,
        y_train=y,
        problem_type="binary",
        mode="long",
    )

    assert automl.max_batches == 6
    assert isinstance(automl._automl_algorithm, DefaultAlgorithm)

    with pytest.raises(ValueError):
        search(
            X_train=X,
            y_train=y,
            problem_type="binary",
            max_time=42,
            patience=3,
            tolerance=0.5,
            mode="everything",
        )
