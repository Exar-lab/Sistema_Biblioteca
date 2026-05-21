"""Domain layer — business entities and domain-level types.

ORM models (SQLAlchemy mappings) are allowed here; they are plain data descriptors
with no runtime side-effects beyond column metadata.

The "no framework imports" rule applies to ports and domain errors: those must not
import HTTP libraries (FastAPI, Starlette), infrastructure adapters, or any
transport/serialization concern.
"""
