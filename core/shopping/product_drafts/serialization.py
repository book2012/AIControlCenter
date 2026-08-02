"""Schema-compatible deterministic ProductDraft serialization."""
from __future__ import annotations
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
import hashlib, json
from typing import Any


def to_json_compatible(value: Any) -> Any:
    if isinstance(value, Enum): return value.value
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00","Z")
    if isinstance(value, Decimal): return format(value, "f")
    if is_dataclass(value):
        result={}
        for f in fields(value):
            child=getattr(value,f.name)
            # Optional proposed fields are absent when not proposed.  Emitting
            # JSON null for these fields would violate the v1 schema (only
            # sale_price and inventory_quantity explicitly admit null).
            if value.__class__.__name__ == "ProposedFields" and child is None:
                continue
            # ProductDraft flattens RevisionIdentity per its v1 schema.
            if f.name == "identity": result.update(to_json_compatible(child))
            else: result[f.name]=to_json_compatible(child)
        return result
    if isinstance(value,(tuple,list)): return [to_json_compatible(x) for x in value]
    if isinstance(value,dict): return {str(k):to_json_compatible(v) for k,v in value.items()}
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(to_json_compatible(value),sort_keys=True,separators=(",",":"),ensure_ascii=False)


def sha256_digest(value: Any) -> str:
    return "sha256:"+hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _dt(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamp must use the UTC Z suffix")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("timestamp must be UTC")
    return parsed


def product_draft_from_dict(data: dict[str,Any]):
    from .models import (ApprovalDecision, DeploymentIntent, ProductDraftRevision, ProposedFields,
        RevisionIdentity, SourceSnapshotReference, SuggestionProvenance, ValidationResult)
    from .values import ActorReference, Reference
    actor=lambda x: ActorReference(**x)
    ident=RevisionIdentity(**{**{k:data[k] for k in ("draft_id","revision_id","revision_number","previous_revision_id","correlation_id","audit_reference")},"created_at":_dt(data["created_at"]),"created_by":actor(data["created_by"])})
    src=SourceSnapshotReference(**{**data["source"],"observed_at":_dt(data["source"]["observed_at"])})
    pf=dict(data["proposed_fields"])
    for k in ("regular_price","sale_price"):
        if pf.get(k) is not None: pf[k]=Decimal(pf[k])
    for k in ("categories","tags","image_references"):
        if k in pf: pf[k]=tuple(Reference(**x) for x in pf[k])
    suggestions=tuple(SuggestionProvenance(**{**x,"suggested_at":_dt(x["suggested_at"])}) for x in data["suggestions"])
    validation=data.get("validation")
    if validation: validation=ValidationResult(**{**validation,"errors":tuple(validation["errors"]),"warnings":tuple(validation["warnings"]),"validated_at":_dt(validation["validated_at"])})
    decision=data.get("human_decision")
    if decision: decision=ApprovalDecision(**{**decision,"reviewer":actor(decision["reviewer"]),"decided_at":_dt(decision["decided_at"])})
    intent=data.get("deployment_intent")
    if intent: intent=DeploymentIntent(**{**intent,"created_by":actor(intent["created_by"]),"created_at":_dt(intent["created_at"])})
    return ProductDraftRevision(ident,src,data["state"],ProposedFields(**pf),suggestions,validation,decision,intent,data.get("schema_version","1.0.0"))


def product_draft_from_json(payload: str): return product_draft_from_dict(json.loads(payload))
