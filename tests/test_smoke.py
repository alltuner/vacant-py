from vacant import Status, check, check_many


def test_check_many_preserves_input_order_and_classifies():
    inputs = ["google.com", "this-is-clearly-not-a-domain.example", ""]
    results = check_many(inputs)
    assert [r.input for r in results] == inputs
    assert results[0].status in {Status.REGISTERED, Status.RESERVED}
    assert results[1].status is Status.INVALID
    assert results[2].status is Status.INVALID


def test_check_single_invalid():
    r = check("nope")
    assert r.status is Status.INVALID
