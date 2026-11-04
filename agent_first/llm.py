"""Chat models the agent can use.

OllamaChat : a local model served by Ollama (tool calling through /api/chat).
ScriptedChat : replays prepared answers; used by the tests and the CI, which have no model.
"""
import json
import os
import urllib.request
from dataclasses import dataclass, field

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")


@dataclass
class ToolCall:
    name: str
    arguments: dict


@dataclass
class Reply:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class OllamaChat:
    """num_ctx and num_thread are kept modest so that a laptop does not overheat (see README)."""

    def __init__(self, model: str, timeout: int = 300, seed: int = 42, num_ctx: int = 4096, num_thread: int | None = None):
        self.model, self.timeout, self.seed = model, timeout, seed
        self.options = {"temperature": 0, "seed": seed, "num_ctx": num_ctx}
        if num_thread:
            self.options["num_thread"] = num_thread

    def chat(self, messages: list[dict], tools: list[dict]) -> Reply:
        body = json.dumps({"model": self.model, "messages": messages, "tools": tools, "stream": False,
                           "options": self.options, "keep_alive": "10m"}).encode()
        req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            msg = json.loads(r.read())["message"]
        calls = []
        for c in msg.get("tool_calls") or []:
            args = c["function"].get("arguments") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"_brut": args}
            calls.append(ToolCall(c["function"]["name"], args))
        return Reply(msg.get("content") or "", calls)


class ScriptedChat:
    """Returns the given replies in order, and records what it was sent."""

    def __init__(self, replies: list[Reply]):
        self.replies, self.received = list(replies), []

    def chat(self, messages, tools) -> Reply:
        self.received.append([dict(m) for m in messages])
        return self.replies.pop(0) if self.replies else Reply("Terminé.")
