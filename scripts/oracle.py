"""Enumerate quota-feasible allocations; minimize exact squared quota error."""
from fractions import Fraction
from itertools import combinations
import json
from pathlib import Path

BASIS = 10000
MAX_TOTAL = (1 << 128) - 1
ROOT = Path(__file__).resolve().parents[1]


def reference(total, weights, mode, cursor):
    if not 2 <= len(weights) <= 16:
        raise ValueError('length')
    if not 0 <= total <= MAX_TOTAL:
        raise ValueError('amount')
    if any(not 0 <= w <= BASIS for w in weights) or sum(weights) != BASIS:
        raise ValueError('weights')
    if mode not in ('Fixed', 'Rotating') or not 0 <= cursor < len(weights):
        raise ValueError('mode/cursor')
    quotas = [Fraction(total * w, BASIS) for w in weights]
    floors = [q.numerator // q.denominator for q in quotas]
    eligible = [i for i, q in enumerate(quotas) if q.denominator != 1]
    deficit = total - sum(floors)
    order = list(range(len(weights)))
    if mode == 'Rotating':
        order = order[cursor:] + order[:cursor]
    rank = {i: p for p, i in enumerate(order)}
    best_key = best = None
    for subset in combinations(eligible, deficit):
        chosen = frozenset(subset)
        allocation = [f + (i in chosen) for i, f in enumerate(floors)]
        score = sum((v * BASIS - total * w) ** 2 for v, w in zip(allocation, weights))
        key = (score, tuple(-int(i in chosen) for i in order))
        if best_key is None or key < best_key:
            best_key, best = key, allocation
    assert best is not None and sum(best) == total
    assert all(f <= v <= f + int(i in eligible)
               for i, (v, f) in enumerate(zip(best, floors)))
    awards = [i for i, (v, f) in enumerate(zip(best, floors)) if v > f]
    next_cursor = cursor
    if mode == 'Rotating' and awards:
        residues = [(total * w) % BASIS for w in weights]
        weakest = min(residues[i] for i in awards)
        last = max((i for i in awards if residues[i] == weakest), key=rank.__getitem__)
        next_cursor = (last + 1) % len(weights)
    return best, next_cursor


def self_check():
    assert reference(1, [5000, 5000, 0], 'Rotating', 0) == ([1, 0, 0], 1)
    assert reference(1, [5000, 5000, 0], 'Rotating', 1) == ([0, 1, 0], 2)
    assert reference(1, [5000, 5000, 0], 'Rotating', 2) == ([1, 0, 0], 1)
    assert reference(0, [5000, 5000], 'Rotating', 1) == ([0, 0], 1)
    assert reference(10000, [1, 9999], 'Rotating', 0) == ([1, 9999], 0)
    # Alabama paradox is a documented limitation, not a promised property.
    assert reference(4, [5556, 3333, 1111], 'Fixed', 0)[0] == [2, 1, 1]
    assert reference(5, [5556, 3333, 1111], 'Fixed', 0)[0] == [3, 2, 0]
    invalid = [(-1, [5000, 5000], 'Fixed', 0),
               (MAX_TOTAL + 1, [5000, 5000], 'Fixed', 0),
               (1, [10000], 'Fixed', 0), (1, [10001, -1], 'Fixed', 0),
               (1, [4000, 5000], 'Fixed', 0), (1, [5000, 5000], 'Fixed', 2)]
    for args in invalid:
        try:
            reference(*args)
        except ValueError:
            continue
        raise AssertionError('reference accepted invalid input')


def cases():
    specs = []
    groups = [[5000, 5000], [10000, 0], [0, 10000], [5000, 5000, 0],
              [0, 5000, 5000], [5000, 0, 5000], [5556, 3333, 1111],
              [1, 1, 9998], [2500] * 4, [2500, 2500, 5000, 0],
              [0, 3333, 3333, 3334]]
    for ws in groups:
        for total in [0, 1, 2, 4, 5, 7, 13, 10000, MAX_TOTAL - 1, MAX_TOTAL]:
            for mode in ['Fixed', 'Rotating']:
                cursor = total % len(ws) if mode == 'Rotating' else len(ws) - 1
                specs.append((total, ws, mode, cursor))
    for total in [0, 1, 7, 8, 15, 16, MAX_TOTAL]:
        specs.extend([(total, [625] * 16, 'Rotating', 7),
                      (total, [625] * 16, 'Fixed', 15)])
    specs.extend([(MAX_TOTAL, [10000] + [0] * 15, 'Rotating', 15),
                  (1, [0] * 15 + [10000], 'Rotating', 0),
                  (3, [1250] * 8, 'Rotating', 6), (7, [1250] * 8, 'Fixed', 7)])
    state = 243
    def draw(limit):
        nonlocal state
        state = (state * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
        return state % limit
    for i in range(128):
        size = 2 + i % 15
        cuts = [0] + sorted(draw(BASIS + 1) for _ in range(size - 1)) + [BASIS]
        ws = [b - a for a, b in zip(cuts, cuts[1:])]
        total = [draw(1000), MAX_TOTAL - draw(1000), draw(17)][i % 3]
        specs.extend([(total, ws, 'Fixed', draw(size)),
                      (total, ws, 'Rotating', draw(size))])
    result = []
    for i, (total, ws, mode, cursor) in enumerate(specs):
        payout, next_cursor = reference(total, ws, mode, cursor)
        result.append(dict(name=f'oracle_{i:03d}', total=str(total), weights=ws,
                           mode=mode, cursor=cursor, payouts=list(map(str, payout)),
                           next_cursor=next_cursor))
    return result


def encoded_vectors():
    return (json.dumps(dict(schema=1, reference='enumeration; exact squared quota error',
                            amount_limit=str(MAX_TOTAL), cases=cases()), indent=2) + '\n').encode()


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--write-vectors', action='store_true')
    a = p.parse_args()
    self_check()
    payload = encoded_vectors()
    target = ROOT / 'fixtures' / 'vectors.json'
    if a.write_vectors:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    elif target.read_bytes() != payload:
        raise SystemExit('Fixture mismatch. Inspect before explicitly regenerating.')
    print(f"Reference checks passed; {len(json.loads(payload)['cases'])} vectors.")
