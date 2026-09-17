"""Errors, value objects, entities, aggregates and events."""

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from core.domain.errors import (
    BusinessRuleViolationError,
    ConflictError,
    DomainError,
    DomainValidationError,
    NotFoundError,
)
from core.domain.value_object import ValueObject
from tests.unit.core.samples import (
    SampleAggregate,
    SampleId,
    SampleProps,
    SampleRenamed,
    make_sample,
)

PAST = datetime(2000, 1, 1, tzinfo=UTC)


@dataclass(frozen=True, slots=True, repr=False)
class Money(ValueObject):
    amount: int
    currency: str


class TestDomainErrors:
    def test_exposes_message_code_and_details(self) -> None:
        error = NotFoundError("Missing.", details={"id": "42"})

        assert str(error) == "Missing."
        assert error.message == "Missing."
        assert error.code == "not_found"
        assert error.details == {"id": "42"}

    def test_explicit_code_overrides_the_default(self) -> None:
        assert ConflictError("Taken.", code="name_taken").code == "name_taken"

    @pytest.mark.parametrize(
        ("error_type", "code"),
        [
            (DomainError, "domain_error"),
            (NotFoundError, "not_found"),
            (ConflictError, "conflict"),
            (BusinessRuleViolationError, "business_rule_violation"),
            (DomainValidationError, "validation_error"),
        ],
    )
    def test_default_codes(self, error_type: type[DomainError], code: str) -> None:
        error = error_type("message")

        assert isinstance(error, DomainError)
        assert error.code == code
        assert error.details == {}


class TestValueObject:
    def test_equality_is_structural(self) -> None:
        assert Money(10, "EUR") == Money(10, "EUR")
        assert Money(10, "EUR") != Money(10, "USD")

    def test_is_immutable(self) -> None:
        money = Money(10, "EUR")

        with pytest.raises(AttributeError):
            money.amount = 20  # type: ignore[misc]

    def test_repr_lists_fields(self) -> None:
        assert repr(Money(10, "EUR")) == "Money(amount=10, currency='EUR')"

    def test_base_class_cannot_be_instantiated(self) -> None:
        with pytest.raises(TypeError):
            ValueObject()


class TestEntityId:
    def test_generate_returns_a_uuid7(self) -> None:
        assert SampleId.generate().value.version == 7


class TestEntity:
    def test_equality_uses_type_and_id_only(self) -> None:
        identifier = SampleId.generate()
        first = SampleAggregate(id_=identifier, props=SampleProps(label="a"))
        second = SampleAggregate(id_=identifier, props=SampleProps(label="b"))

        assert first == second
        assert hash(first) == hash(second)
        assert first != make_sample()

    def test_validate_runs_at_construction(self) -> None:
        with pytest.raises(DomainValidationError):
            make_sample(label="")

    def test_updated_at_defaults_to_created_at(self) -> None:
        aggregate = SampleAggregate(
            id_=SampleId.generate(), props=SampleProps(label="a"), created_at_=PAST
        )

        assert aggregate.updated_at_ == PAST

    def test_touch_refreshes_updated_at_only(self) -> None:
        aggregate = SampleAggregate(
            id_=SampleId.generate(), props=SampleProps(label="a"), created_at_=PAST
        )

        aggregate.rename("b")

        assert aggregate.created_at_ == PAST
        assert aggregate.updated_at_ > PAST

    def test_id_is_read_only(self) -> None:
        aggregate = make_sample()

        with pytest.raises(AttributeError):
            aggregate.id_ = SampleId.generate()  # type: ignore[misc]


class TestAggregateRoot:
    def test_pull_events_returns_then_forgets_recorded_events(self) -> None:
        aggregate = make_sample()
        aggregate.rename("second")

        events = aggregate.pull_events()

        assert [type(event) for event in events] == [SampleRenamed]
        assert aggregate.pull_events() == []

    def test_events_have_an_identity_and_a_utc_timestamp(self) -> None:
        event = SampleRenamed(label="x")

        assert event.event_id.version == 7
        assert event.occurred_at.tzinfo is UTC
