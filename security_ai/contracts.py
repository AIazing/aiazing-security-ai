"""Validate repository-owned contracts without fetching external schemas."""

from functools import lru_cache
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


@lru_cache(maxsize=1)
def validators():
    directory = Path(__file__).resolve().parent.parent / "schemas"
    documents = {}
    for path in directory.glob("*.schema.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        document["$id"] = path.as_uri()
        Draft202012Validator.check_schema(document)
        documents[path.name] = document
    registry = Registry().with_resources(
        (document["$id"], Resource.from_contents(document))
        for document in documents.values()
    )
    return {
        name: Draft202012Validator(document, registry=registry,
                                  format_checker=FormatChecker())
        for name, document in documents.items()
    }


def valid(document, schema):
    return validators()[schema].is_valid(document)


def validate_result(document):
    # Do not include validator exception text: it can echo sensitive instance data.
    if not valid(document, "assessment-result.schema.json"):
        raise RuntimeError("Generated assessment result does not satisfy its contract")
