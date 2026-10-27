from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from src.data_validation.schemas import (
    DataStatus,
    FinancialObservationSchema,
    StatementType,
)


def valid_observation(**overrides):
    data = {
        "company_id": 1,
        "statement_type": StatementType.INCOME_STATEMENT,
        "reporting_date": date(2025, 12, 31),
        "metric_name": "Total Revenue",
        "value": 100.0,
        "status": DataStatus.REPORTED,
        "currency": "USD",
        "unit": "millions",
        "source": "yfinance",
        "ingested_at": datetime.now(timezone.utc),
        "ingestion_run_id": "test-run",
    }

    data.update(overrides)

    return data


def test_valid_reported_observation_passes():
    observation = FinancialObservationSchema.model_validate(
        valid_observation()
    )

    assert observation.value == 100.0
    assert observation.status == DataStatus.REPORTED


def test_reported_zero_is_preserved():
    observation = FinancialObservationSchema.model_validate(
        valid_observation(value=0.0)
    )

    assert observation.value == 0.0
    assert observation.status == DataStatus.REPORTED


def test_missing_value_can_be_represented():
    observation = FinancialObservationSchema.model_validate(
        valid_observation(
            value=None,
            status=DataStatus.MISSING,
        )
    )

    assert observation.value is None
    assert observation.status == DataStatus.MISSING


def test_not_applicable_value_can_be_represented():
    observation = FinancialObservationSchema.model_validate(
        valid_observation(
            value=None,
            status=DataStatus.NOT_APPLICABLE,
        )
    )

    assert observation.value is None
    assert observation.status == DataStatus.NOT_APPLICABLE


def test_provider_unsupplied_value_can_be_represented():
    observation = FinancialObservationSchema.model_validate(
        valid_observation(
            value=None,
            status=DataStatus.NOT_SUPPLIED,
        )
    )

    assert observation.value is None
    assert observation.status == DataStatus.NOT_SUPPLIED


def test_metric_name_is_normalized():
    observation = FinancialObservationSchema.model_validate(
        valid_observation(metric_name="  Total Revenue  ")
    )

    assert observation.metric_name == "Total Revenue"


def test_blank_metric_name_is_rejected():
    with pytest.raises(ValidationError):
        FinancialObservationSchema.model_validate(
            valid_observation(metric_name="   ")
        )


def test_blank_source_is_rejected():
    with pytest.raises(ValidationError):
        FinancialObservationSchema.model_validate(
            valid_observation(source="   ")
        )


def test_unknown_fields_are_rejected():
    data = valid_observation()
    data["unexpected_field"] = "not allowed"

    with pytest.raises(ValidationError):
        FinancialObservationSchema.model_validate(data)
