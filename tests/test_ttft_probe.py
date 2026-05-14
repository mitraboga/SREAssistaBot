from evals.run_ttft_probe import event_has_text, parse_sse_data


def test_parse_sse_data_extracts_json_payload():
    event = parse_sse_data(b'data: {"content":{"parts":[{"text":"hello"}]}}\n')

    assert event == {"content": {"parts": [{"text": "hello"}]}}


def test_event_has_text_detects_adk_text_event():
    assert event_has_text({"content": {"parts": [{"text": "hello"}]}}) is True
    assert event_has_text({"error": "model failed"}) is False

