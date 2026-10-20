"""Bounded verification of reviewed, conjunctive scientific claims.

Alternative bundles are mutually exclusive, not independent facts. Context IDs
must encode every material experimental condition. No text extraction is implied.
"""
from dataclasses import asdict, dataclass, replace
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from math import prod


@dataclass(frozen=True)
class Fact:
    entity: str
    metric: str
    unit: str
    value: str
    context: str
    source: str


@dataclass(frozen=True)
class Atom:
    entity: str
    metric: str
    unit: str
    operator: str
    value: str


@dataclass(frozen=True)
class Choice:
    locator: str
    alternatives: tuple[tuple[Fact, ...], ...]
    cost: int = 1


@dataclass(frozen=True)
class Problem:
    atoms: tuple[Atom, ...]
    contexts: tuple[str, ...]
    facts: tuple[Fact, ...] = ()
    choices: tuple[Choice, ...] = ()
    closed_domain: bool = False


def number(value):
    if not isinstance(value, str):
        raise ValueError('Use decimal strings, not floating-point inputs.')
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError('Invalid decimal string.') from exc
    if not result.is_finite():
        raise ValueError('Numbers must be finite.')
    return result


def validate(p):
    if not p.atoms or not p.contexts or len(set(p.contexts)) != len(p.contexts):
        raise ValueError('Nonempty atoms and unique explicit contexts required.')
    if any(not isinstance(c, str) or not c.strip() for c in p.contexts):
        raise ValueError('Context IDs must be nonempty strings.')
    if type(p.closed_domain) is not bool:
        raise ValueError('closed_domain must be boolean.')
    for a in p.atoms:
        if a.operator not in ('==', '>=', '<=', '>', '<'):
            raise ValueError('Unsupported comparison operator.')
        number(a.value)
        if not all((a.entity, a.metric, a.unit)):
            raise ValueError('Entity, metric and unit required.')
    bundles = [(-1, 0, p.facts)]
    for i, c in enumerate(p.choices):
        if not c.locator or type(c.cost) is not int or c.cost <= 0 or not c.alternatives:
            raise ValueError('Choices need a source locator, positive integer cost and alternatives.')
        bundles.extend((i, j, facts) for j, facts in enumerate(c.alternatives))
    # Reject conflicting potentially coexisting measurements, rather than resolve
    # disagreements silently. Alternatives in the SAME block cannot coexist.
    seen = {}
    for block, alt, facts in bundles:
        for f in facts:
            value = number(f.value)
            if not all((f.entity, f.metric, f.unit, f.source)) or f.context not in p.contexts:
                raise ValueError('Facts need provenance and a declared context.')
            key = (f.entity, f.metric, f.unit, f.context)
            for oldblock, oldalt, oldvalue in seen.get(key, []):
                exclusive = block == oldblock and alt != oldalt
                if not exclusive and oldvalue != value:
                    raise ValueError('Conflicting potentially coexisting measurements.')
            seen.setdefault(key, []).append((block, alt, value))


def _signature(p, facts):
    masks = [0] * (2 * len(p.contexts))
    for f in facts:
        context = p.contexts.index(f.context)
        for i, a in enumerate(p.atoms):
            if (a.entity, a.metric, a.unit) != (f.entity, f.metric, f.unit):
                continue
            x, y = number(f.value), number(a.value)
            ok = {'==': x == y, '>=': x >= y, '<=': x <= y, '>': x > y, '<': x < y}[a.operator]
            masks[2 * context + (0 if ok else 1)] |= 1 << i
    return tuple(masks)


def _decision(p, signature):
    full = (1 << len(p.atoms)) - 1
    if any(signature[i] == full for i in range(0, len(signature), 2)):
        return 'supported'
    if p.closed_domain and all(signature[i] for i in range(1, len(signature), 2)):
        return 'contradicted'
    return 'insufficient'


def audit(p, max_states=100000):
    """Exact DP over satisfaction signatures; counts are NOT probabilities."""
    validate(p)
    if type(max_states) is not int or max_states < 1:
        raise ValueError('max_states must be a positive integer.')
    states = {_signature(p, p.facts): (1, ())}
    widths = [1]
    transitions = 0
    for choice in p.choices:
        updated = {}
        signatures = [_signature(p, a) for a in choice.alternatives]
        for state, (count, witness) in states.items():
            for j, signature in enumerate(signatures):
                transitions += 1
                merged = tuple(a | b for a, b in zip(state, signature))
                oldcount, representative = updated.get(merged, (0, witness + (j,)))
                updated[merged] = (oldcount + count, representative)
                if len(updated) > max_states:
                    return {'status': 'incomplete', 'reason': 'State budget exceeded; no verdict issued.'}
        states = updated
        widths.append(len(states))
    counts, witnesses = {}, {}
    for signature, (count, witness) in states.items():
        verdict = _decision(p, signature)
        counts[verdict] = counts.get(verdict, 0) + count
        witnesses.setdefault(verdict, list(witness))
    digest = sha256(json.dumps(asdict(p), sort_keys=True).encode()).hexdigest()
    return {'status': next(iter(counts)) if len(counts) == 1 else 'ambiguous',
            'world_counts': counts, 'representative_bindings': witnesses,
            'worlds': prod(len(c.alternatives) for c in p.choices),
            'state_widths': widths, 'transitions': transitions,
            'input_sha256': digest, 'policy': 'scope-v1'}


def recommend_resolution(p, max_states=100000):
    """Recommend cheapest single header whose resolution guarantees a decision.

    Inspect all outcomes; never infer which header interpretation is correct.
    Return None when no single acquisition is sufficient (including budget caps).
    """
    if audit(p, max_states)['status'] != 'ambiguous':
        return None
    candidates = []
    for i, c in enumerate(p.choices):
        outcomes = [audit(replace(p, facts=p.facts + facts,
                    choices=p.choices[:i] + p.choices[i+1:]), max_states)['status']
                    for facts in c.alternatives]
        if all(s in ('supported', 'contradicted', 'insufficient') for s in outcomes):
            candidates.append({'choice_index': i, 'source_locator': c.locator,
                               'cost': c.cost, 'conditional_statuses': outcomes})
    return min(candidates, key=lambda c: (c['cost'], c['choice_index'])) if candidates else None


def from_dict(data):
    return Problem(atoms=tuple(Atom(**a) for a in data['atoms']),
                   contexts=tuple(data['contexts']),
                   facts=tuple(Fact(**f) for f in data.get('facts', [])),
                   choices=tuple(Choice(c['locator'], tuple(tuple(Fact(**f) for f in alt)
                       for alt in c['alternatives']), c.get('cost', 1)) for c in data.get('choices', [])),
                   closed_domain=data.get('closed_domain', False))


def verify_replay(record):
    """Recompute a saved audit; integrity check, not source authentication."""
    try:
        return audit(from_dict(record['input'])) == record['result']
    except (ValueError, KeyError, TypeError):
        return False
