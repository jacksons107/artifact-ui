from system_spec_ir import validate_spec, compile_ir, has_behavioral
from system_spec_examples import EXAMPLES


AUTH_SPEC = EXAMPLES["sys_behavioral_auth"]


def test_has_behavioral():
    assert has_behavioral(AUTH_SPEC)
    assert not has_behavioral({"nodes": [{"id": "a", "label": "A"}]})


def test_validate_and_compile_auth_flow():
    spec = validate_spec(AUTH_SPEC)
    ir = compile_ir(spec)

    place_ids = {p["id"] for p in ir["net"]["places"]}
    assert {"LoginRequest", "AuthenticatedUser", "Session"} <= place_ids

    transition_ids = {t["id"] for t in ir["net"]["transitions"]}
    assert {"validate_credentials", "create_session"} <= transition_ids

    assert ir["net"]["initial_marking"] == ["LoginRequest"]


def test_failure_mode_expansion():
    spec = validate_spec(AUTH_SPEC)
    ir = compile_ir(spec)
    transitions = {t["id"]: t for t in ir["net"]["transitions"]}

    # auth_db has unavailable + stale_read failure modes
    assert "auth_db__unavailable" in transitions
    unavail = transitions["auth_db__unavailable"]
    assert unavail["synthetic"] is True
    assert "availability" in unavail["tags"]
    assert "db-failure" in unavail["tags"]
    assert unavail["out"] == ["auth_db__error"]

    # stale_read expands the validate_credentials transition (it `reads` auth_db)
    stale_id = "validate_credentials__stale_auth_db"
    assert stale_id in transitions
    assert "stale_read" in transitions[stale_id]["tags"]

    # session_cache only declares "unavailable"
    assert "session_cache__unavailable" in transitions
    assert "session_cache__stale_read" not in transitions

    # synthetic error place was created
    place_ids = {p["id"] for p in ir["net"]["places"]}
    assert "auth_db__error" in place_ids


def test_tags_index_and_meta():
    spec = validate_spec(AUTH_SPEC)
    ir = compile_ir(spec)

    assert "validate_credentials" in ir["tags_index"]["auth"]["transitions"]
    assert "create_session" in ir["tags_index"]["auth"]["transitions"]
    assert ir["meta"]["transition_to_node"]["validate_credentials"] == "auth_service"
    assert "validate_credentials" in ir["meta"]["node_to_transitions"]["auth_service"]


def test_invariants_normalized_and_hold():
    spec = validate_spec(AUTH_SPEC)
    ir = compile_ir(spec)
    invariants = {i["id"]: i for i in ir["invariants"]}

    auth_before_db = invariants["auth_before_db_read"]
    assert auth_before_db["rule"]["type"] == "precedes"
    assert "validate_credentials" in auth_before_db["rule"]["before"]
    assert "validate_credentials" in auth_before_db["rule"]["after"]

    session_requires_auth = invariants["session_requires_auth"]
    assert session_requires_auth["rule"]["before"] == ["validate_credentials"]
    assert session_requires_auth["rule"]["after"] == ["create_session"]


def test_violating_invariant_produces_counterexample():
    """A 'requires' invariant referencing an action that never runs first should
    be detectable as a violation by a simple trace-level checker (mirrors the
    in-browser logic in system_spec_ir_js.IR_JS)."""
    spec_data = {
        "title": "Order Flow",
        "nodes": [
            {"id": "checkout", "label": "Checkout", "kind": "service"},
        ],
        "data": [
            {"id": "Order", "label": "Order", "schema": {}, "example": {}},
            {"id": "ShippedOrder", "label": "Shipped Order", "schema": {}, "example": {}},
        ],
        "actions": [
            {"id": "ship_order", "label": "Ship Order", "node": "checkout",
             "consumes": ["Order"], "produces": ["ShippedOrder"], "tags": ["shipping"]},
        ],
        "invariants": [
            {"id": "ship_after_payment", "label": "Orders cannot ship before payment",
             "rule": {"type": "requires", "before": {"tag": "payment"}, "after": {"action": "ship_order"}},
             "severity": "high"},
        ],
        "initial_tokens": ["Order"],
    }
    spec = validate_spec(spec_data)
    ir = compile_ir(spec)
    inv = ir["invariants"][0]

    assert inv["rule"]["before"] == []  # no transition is tagged "payment"
    assert inv["rule"]["after"] == ["ship_order"]

    # Simulate the JS 'requires' check: ship_order fires with no prior 'payment'-tagged step.
    trace = ["ship_order"]
    before_set, after_set = set(inv["rule"]["before"]), set(inv["rule"]["after"])
    seen_before = False
    violation = None
    for i, tid in enumerate(trace):
        if tid in before_set:
            seen_before = True
        if tid in after_set and not seen_before:
            violation = i
            break
    assert violation == 0


def test_invalid_action_reference_raises():
    bad = {
        "title": "Bad Spec",
        "nodes": [{"id": "svc", "label": "Service", "kind": "service"}],
        "data": [{"id": "X", "label": "X"}],
        "actions": [{"id": "do_thing", "label": "Do Thing", "node": "svc",
                      "consumes": ["X"], "produces": ["DOES_NOT_EXIST"]}],
    }
    try:
        validate_spec(bad)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_invalid_failure_mode_raises():
    bad = {
        "title": "Bad Spec",
        "nodes": [{"id": "svc", "label": "Service", "kind": "service", "failure_modes": ["message_drop"]}],
    }
    try:
        validate_spec(bad)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


if __name__ == "__main__":
    import sys
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    sys.exit(1 if failed else 0)
