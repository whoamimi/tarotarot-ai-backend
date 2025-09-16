import pytest
from types import SimpleNamespace

import src.model_chain as mc
from src.client import OPTIONS as DEFAULT_OPTIONS

class DummyTask:
    """ A dummy TaroAction-like object with a label and an action_prompt method. """
    label = "dummy"

    @staticmethod
    def action_prompt(**inputs):
        # Return a simple stream of dicts to emulate LLM messages
        yield {"role": "system", "content": "init"}
        yield {"role": "user",   "content": str(inputs)}

class DummyClient:
    """ A dummy client with a chat(...) method. """
    def __init__(self, response_text: str):
        self._response = response_text

    def chat(self, *, model, messages, stream, options):
        # Return an object with a .message dict
        return SimpleNamespace(message={"content": self._response})

@pytest.fixture(autouse=True)
def patch_task(monkeypatch: pytest.MonkeyPatch):
    # Patch taro.get_jawa(...) to always return DummyTask
    monkeypatch.setattr(mc, "taro", SimpleNamespace(get_jawa=lambda name: DummyTask()))
    yield

@pytest.fixture(autouse=True)
def patch_setup_client(monkeypatch: pytest.MonkeyPatch):
    # By default, patch setup_client() to return a DummyClient
    def fake_setup_client():
        return DummyClient("ok")
    monkeypatch.setattr(mc, "setup_client", lambda: fake_setup_client())
    yield

def test_registry_contains_combinationanalyst():
    # Ensure that subclassing registered it
    assert "CombinationAnalyst" in mc.SandCrawler.registry

def test_feature_augment_roundtrips_kwargs():
    ca = mc.CombinationAnalyst()
    data = {"foo": 1, "bar": "baz"}
    assert ca.feature_augment(**data) == data

def test_process_builds_message_from_task():
    ca = mc.CombinationAnalyst()
    # Replace its task with our dummy
    ca.task = DummyTask()
    result = ca.process(alpha=42)
    # Expect the two-message stream from DummyTask.action_prompt
    assert isinstance(result, list)
    assert result[0] == {"role": "system", "content": "init"}
    # The user message should contain our inputs
    assert result[1]["role"] == "user"
    assert "alpha" in result[1]["content"]

def test_run_invokes_client_and_returns_content(monkeypatch: pytest.MonkeyPatch):
    # Arrange a CombinationAnalyst and patch its process() to return a fake message list
    ca = mc.CombinationAnalyst()
    fake_messages = [{"role":"user","content":"hello"}]
    monkeypatch.setattr(ca, "process", lambda **kwargs: fake_messages)

    # Create a fake client whose .chat returns a known string
    class ChatObj:
        message = {"content": "response text"}
    monkeypatch.setattr(mc, "setup_client", lambda: SimpleNamespace(chat=lambda **kw: ChatObj()))

    output = ca.run(foo="bar")
    assert output == "response text"

def test_decode_kwargs_setter_and_getter():
    ca = mc.CombinationAnalyst()
    # Default decode_kwargs is the same type as mc.OPTIONS

    assert isinstance(ca.decode_kwargs, type(DEFAULT_OPTIONS))

    # Update with new params
    ca.decode_kwargs = {"num_ctx": 3000, "num_keep": 10}
    new_decode = ca.decode_kwargs

    assert new_decode["num_keep"] == 10 and new_decode["num_ctx"] == 3000
    # Setting to non-dict should raise

    with pytest.raises(KeyError) as excinfo:
        # Setting an unrecognized decode option should raise TypeError
        ca.decode_kwargs = {'mima': 30000}
    assert "Unknown decode option: 'mima'" in str(excinfo.value)


def test_run_calls_setup_client_and_passes_parameters(monkeypatch):
    # Prepare a fake CombinationAnalyst and its process() output
    ca = mc.CombinationAnalyst()
    fake_messages = [{"role": "user", "content": "ping"}]
    monkeypatch.setattr(ca, "process", lambda **kwargs: fake_messages)

    # Capture the parameters passed into chat()
    captured = {}
    def fake_chat(*, model, messages, stream, options):
        captured.update({
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": options
        })
        return SimpleNamespace(message={"content": "pong"})

    # Patch setup_client() to return our dummy client
    monkeypatch.setattr(mc, "setup_client", lambda: SimpleNamespace(chat=fake_chat))

    # Call run() and assert return value
    result = ca.run(test_arg=42)
    assert result == "pong"

    # Assert chat() was called with the expected arguments
    assert captured["model"] == mc.LLM_MODEL_ID
    assert captured["messages"] == fake_messages
    assert captured["stream"] is False
    # The passed options object should be exactly the instance on ca
    assert captured["options"] is ca.decode_kwargs
