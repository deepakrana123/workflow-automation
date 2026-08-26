"""Unit tests for workspace ancestor-chain resolution (pure version)."""

from app.rbac.hierarchy import get_ancestor_chain_pure


def _ws(id_, level, parent_id=None):
    return {"id": id_, "level": level, "parent_id": parent_id}


def _build(workspaces):
    return {w["id"]: w for w in workspaces}


# ── get_ancestor_chain_pure ───────────────────────────────────────────────────

def test_branch_returns_full_chain():
    wss = _build([
        _ws(1, "global"),
        _ws(2, "region", 1),
        _ws(3, "zone",   2),
        _ws(4, "branch", 3),
    ])
    assert get_ancestor_chain_pure(4, wss) == [1, 2, 3, 4]


def test_global_returns_only_itself():
    wss = _build([_ws(1, "global")])
    assert get_ancestor_chain_pure(1, wss) == [1]


def test_region_returns_two():
    wss = _build([_ws(1, "global"), _ws(2, "region", 1)])
    assert get_ancestor_chain_pure(2, wss) == [1, 2]


def test_missing_parent_stops_chain():
    # Parent 99 does not exist — chain should still return what it found
    wss = _build([_ws(5, "branch", 99)])
    chain = get_ancestor_chain_pure(5, wss)
    assert 5 in chain


def test_cycle_does_not_loop_forever():
    # Artificially create a cycle (should never happen in DB, but must be safe)
    wss = _build([_ws(1, "region", 2), _ws(2, "zone", 1)])
    chain = get_ancestor_chain_pure(1, wss)
    # Just verify it terminates without error and returns something
    assert isinstance(chain, list)


def test_unknown_workspace_returns_empty():
    wss = _build([_ws(1, "global")])
    assert get_ancestor_chain_pure(99, wss) == []
