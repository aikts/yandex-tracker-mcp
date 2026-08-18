"""Guard: entity models must speak Tracker's own field names on the wire."""

import importlib
import inspect
import pkgutil

import pytest
from pydantic import BaseModel

import mcp_tracker.tracker.proto.types as types_package


def _aliased_fields() -> list[tuple[str, str, list[str], str | None]]:
    """Collect (model, field, validation aliases, serialization alias) triples."""
    collected: list[tuple[str, str, list[str], str | None]] = []
    for module_info in pkgutil.iter_modules(types_package.__path__):
        module = importlib.import_module(f"{types_package.__name__}.{module_info.name}")
        for obj in vars(module).values():
            if (
                not inspect.isclass(obj)
                or not issubclass(obj, BaseModel)
                or obj.__module__ != module.__name__
            ):
                continue
            for field_name, field in obj.model_fields.items():
                aliases = getattr(field.validation_alias, "choices", None)
                if aliases is None:
                    continue
                collected.append(
                    (obj.__name__, field_name, list(aliases), field.serialization_alias)
                )
    return collected


ALIASED_FIELDS = _aliased_fields()


class TestModelAliases:
    def test_models_declare_aliases(self) -> None:
        assert ALIASED_FIELDS, (
            "no aliased fields discovered - the sweep below is vacuous"
        )

    @pytest.mark.parametrize(
        ("model", "field", "aliases", "serialization_alias"),
        ALIASED_FIELDS,
        ids=[f"{model}.{field}" for model, field, _, _ in ALIASED_FIELDS],
    )
    def test_serializes_under_the_tracker_name(
        self,
        model: str,
        field: str,
        aliases: list[str],
        serialization_alias: str | None,
    ) -> None:
        """A field that accepts Tracker's name must also emit it.

        Otherwise a response can not be fed back into a write call: the reader
        would get `story_points` while `fields` expects `storyPoints`.
        """
        wire_name = aliases[0]
        if wire_name == field:
            pytest.skip("field name already matches the Tracker name")
        assert serialization_alias == wire_name, (
            f"{model}.{field} accepts '{wire_name}' but serializes as "
            f"'{serialization_alias or field}'"
        )
