from __future__ import annotations

import pytest

from DataStandardization.artifact import CanonicalArtifact, OperationType, OriginalValue, Transformation
from DataStandardization.mapper import FieldMapper
from DataStandardization.normalizer import NormalizationRule, Normalizer
from DataStandardization.schema import FieldSpec, Schema
from DataStandardization.standardize import reconstruct_original, standardize
from DataStandardization.validator import Validator


def build_schema() -> Schema:
    return Schema(
        [
            FieldSpec("customer_id", value_type=str, required=True, aliases=("cust_id",)),
            FieldSpec("full_name", value_type=str),
            FieldSpec("email", value_type=str),
            FieldSpec("join_date", value_type=str),
            FieldSpec("status", allowed_values=("active", "inactive")),
            FieldSpec("score", value_type=int),
        ]
    )


class TestSchema:
    def test_resolve_canonical_name(self):
        schema = build_schema()
        spec = schema.resolve("customer_id")
        assert spec is not None
        assert spec.canonical_name == "customer_id"

    def test_resolve_alias(self):
        schema = build_schema()
        spec = schema.resolve("cust_id")
        assert spec is not None
        assert spec.canonical_name == "customer_id"

    def test_resolve_unknown_returns_none(self):
        schema = build_schema()
        assert schema.resolve("nope") is None

    def test_fields_exposes_field_specs(self):
        schema = build_schema()
        assert [f.canonical_name for f in schema.fields] == [
            "customer_id",
            "full_name",
            "email",
            "join_date",
            "status",
            "score",
        ]


class TestFieldMapper:
    def test_apply_renames_alias(self):
        mapper = FieldMapper(build_schema())
        output, transformations = mapper.apply({"cust_id": "A1", "full_name": "Ann"})
        assert output == {"customer_id": "A1", "full_name": "Ann"}
        assert len(transformations) == 1
        transformation = transformations[0]
        assert transformation.operation == "rename_field"
        assert transformation.operation_type is OperationType.REVERSIBLE
        assert transformation.field == "customer_id"
        assert transformation.rule == ("cust_id",)

    def test_apply_keeps_canonical_name(self):
        mapper = FieldMapper(build_schema())
        output, transformations = mapper.apply({"customer_id": "A1"})
        assert output == {"customer_id": "A1"}
        assert transformations == ()

    def test_apply_passes_through_unknown_fields(self):
        mapper = FieldMapper(build_schema())
        output, transformations = mapper.apply({"extra": 1, "customer_id": "A1"})
        assert output == {"extra": 1, "customer_id": "A1"}
        assert transformations == ()

    def test_apply_inverse_restores_first_alias(self):
        mapper = FieldMapper(build_schema())
        output = mapper.apply_inverse({"customer_id": "A1", "full_name": "Ann"})
        assert output == {"cust_id": "A1", "full_name": "Ann"}

    def test_apply_inverse_keeps_unknown_fields(self):
        mapper = FieldMapper(build_schema())
        assert mapper.apply_inverse({"extra": 1}) == {"extra": 1}


class TestTransformation:
    def test_reversible_requires_rule(self):
        with pytest.raises(ValueError, match="REVERSIBLE"):
            Transformation(operation_type=OperationType.REVERSIBLE, operation="trim", field="x")

    def test_lossy_requires_before_and_after(self):
        with pytest.raises(ValueError, match="LOSSY"):
            Transformation(
                operation_type=OperationType.LOSSY,
                operation="trim",
                field="x",
                before=OriginalValue("  v  "),
            )

    def test_lossy_rejects_non_original_value_before(self):
        with pytest.raises(ValueError, match="LOSSY"):
            Transformation(
                operation_type=OperationType.LOSSY,
                operation="trim",
                field="x",
                before="  v  ",
                after="v",
            )


class TestNormalizer:
    def _normalize(self, record, rules):
        normalizer = Normalizer(build_schema(), tuple(rules))
        return normalizer.normalize(record)

    def test_collapse_whitespace_is_lossy(self):
        output, transformations = self._normalize(
            {"full_name": "  Ann   Marie "}, [NormalizationRule("full_name", "collapse_whitespace")]
        )
        assert output["full_name"] == "Ann Marie"
        transformation = transformations[0]
        assert transformation.operation_type is OperationType.LOSSY
        assert transformation.before.value == "  Ann   Marie "
        assert transformation.after == "Ann Marie"

    def test_trim(self):
        output, transformations = self._normalize(
            {"full_name": "  Ann  "}, [NormalizationRule("full_name", "trim")]
        )
        assert output["full_name"] == "Ann"
        assert transformations[0].operation_type is OperationType.LOSSY

    def test_casefold(self):
        output, _ = self._normalize({"email": "Ann@MAIL.com"}, [NormalizationRule("email", "casefold")])
        assert output["email"] == "ann@mail.com"

    def test_strip_prefix_is_reversible(self):
        output, transformations = self._normalize(
            {"customer_id": "CUST-42"}, [NormalizationRule("customer_id", "strip_prefix", ("CUST-",))]
        )
        assert output["customer_id"] == "42"
        transformation = transformations[0]
        assert transformation.operation_type is OperationType.REVERSIBLE
        assert transformation.rule == ("CUST-",)

    def test_strip_prefix_noop_when_prefix_absent(self):
        output, transformations = self._normalize(
            {"customer_id": "42"}, [NormalizationRule("customer_id", "strip_prefix", ("CUST-",))]
        )
        assert output["customer_id"] == "42"
        assert transformations == ()

    def test_strip_suffix(self):
        output, transformations = self._normalize(
            {"email": "ann@mail.com "}, [NormalizationRule("email", "strip_suffix", (" ",))]
        )
        assert output["email"] == "ann@mail.com"
        assert transformations[0].operation_type is OperationType.REVERSIBLE

    def test_reformat_date(self):
        output, transformations = self._normalize(
            {"join_date": "2024-03-01"},
            [NormalizationRule("join_date", "reformat_date", ("%Y-%m-%d", "%d/%m/%Y"))],
        )
        assert output["join_date"] == "01/03/2024"
        assert transformations[0].operation_type is OperationType.REVERSIBLE

    def test_no_transformation_when_value_unchanged(self):
        output, transformations = self._normalize(
            {"email": "ann@mail.com"}, [NormalizationRule("email", "casefold")]
        )
        assert output["email"] == "ann@mail.com"
        assert transformations == ()

    def test_rule_resolves_alias_to_canonical_field(self):
        output, _ = self._normalize(
            {"customer_id": "CUST-1"}, [NormalizationRule("cust_id", "strip_prefix", ("CUST-",))]
        )
        assert output["customer_id"] == "1"

    def test_unknown_field_raises(self):
        with pytest.raises(ValueError, match="unknown field"):
            self._normalize({"full_name": "Ann"}, [NormalizationRule("nope", "trim")])

    def test_unknown_operation_raises(self):
        with pytest.raises(ValueError, match="unknown normalization operation"):
            self._normalize({"full_name": "Ann"}, [NormalizationRule("full_name", "nope")])


class TestValidator:
    def test_valid_record(self):
        report = Validator(build_schema()).validate(
            {"cust_id": "A1", "full_name": "Ann", "status": "active", "score": 5}
        )
        assert report.valid is True
        assert report.errors == ()
        assert report.warnings == ()

    def test_missing_required_field(self):
        report = Validator(build_schema()).validate({"full_name": "Ann"})
        assert report.valid is False
        assert "missing required field: customer_id" in report.errors

    def test_required_field_null(self):
        report = Validator(build_schema()).validate({"customer_id": None})
        assert report.valid is False
        assert "required field is null: customer_id" in report.errors

    def test_type_mismatch(self):
        report = Validator(build_schema()).validate({"customer_id": "A1", "score": "high"})
        assert report.valid is False
        assert any("score" in error and "expected int" in error for error in report.errors)

    def test_disallowed_value(self):
        report = Validator(build_schema()).validate({"customer_id": "A1", "status": "banned"})
        assert report.valid is False
        assert any("status" in error and "not allowed" in error for error in report.errors)

    def test_unknown_field_produces_warning(self):
        report = Validator(build_schema()).validate({"customer_id": "A1", "bogus": 1})
        assert report.valid is True
        assert report.warnings == ("unknown field: bogus",)


class TestStandardize:
    def test_standardize_returns_canonical_artifact(self):
        schema = build_schema()
        artifact = standardize(
            {"cust_id": "CUST-42", "full_name": "  Ann   Marie  "},
            schema,
            [NormalizationRule("full_name", "collapse_whitespace")],
        )
        assert isinstance(artifact, CanonicalArtifact)
        assert artifact.canonical_data["customer_id"] == "CUST-42"
        assert artifact.canonical_data["full_name"] == "Ann Marie"

    def test_standardize_preserves_order_of_transformations(self):
        schema = build_schema()
        artifact = standardize(
            {"cust_id": "CUST-42", "full_name": "  Ann  "},
            schema,
            [NormalizationRule("full_name", "trim")],
        )
        assert [t.operation for t in artifact.transformations] == ["rename_field", "trim"]

    def test_reconstruct_original_round_trip(self):
        schema = build_schema()
        artifact = standardize(
            {"cust_id": "CUST-42", "full_name": "  Ann  "},
            schema,
            [NormalizationRule("full_name", "trim")],
        )
        original = reconstruct_original(artifact)
        assert original == {"cust_id": "CUST-42", "full_name": "  Ann  "}

    def test_reconstruct_original_restores_lossy_values_from_before(self):
        schema = build_schema()
        artifact = standardize(
            {"full_name": "  Ann  "}, schema, [NormalizationRule("full_name", "collapse_whitespace")]
        )
        original = reconstruct_original(artifact)
        assert original["full_name"] == "  Ann  "

    def test_reconstruct_original_inverts_reversible_operations(self):
        schema = build_schema()
        artifact = standardize(
            {"cust_id": "CUST-42"},
            schema,
            [NormalizationRule("customer_id", "strip_prefix", ("CUST-",))],
        )
        original = reconstruct_original(artifact)
        assert original["cust_id"] == "CUST-42"
