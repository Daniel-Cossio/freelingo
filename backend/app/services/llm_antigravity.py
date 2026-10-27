from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from app.services.llm_adapter import (
    LLMError,
    LLMResponseError,
    LLMTimeoutError,
    LLMUnavailableError,
)

logger = logging.getLogger(__name__)


class ChunkDelta:
    __slots__ = ("content",)

    def __init__(self, content: str) -> None:
        self.content = content


class ChunkChoice:
    __slots__ = ("delta",)

    def __init__(self, content: str) -> None:
        self.delta = ChunkDelta(content)


class AntigravityStreamChunk:
    __slots__ = ("choices", "_content")

    def __init__(self, content: str) -> None:
        self._content = content
        self.choices = [ChunkChoice(content)]

    def __str__(self) -> str:
        return self._content


class AntigravityStream:
    """Async generator yielding chunks from agy's stream-json output."""

    def __init__(
        self,
        process: asyncio.subprocess.Process,
        timeout: float = 120.0,
    ) -> None:
        self.process = process
        self.timeout = timeout
        self.prompt_tokens: int | None = None
        self.completion_tokens: int | None = None
        self.total_tokens: int | None = None
        self.status: str | None = None

    def __aiter__(self) -> AsyncGenerator[AntigravityStreamChunk, None]:
        return self._iterate()

    async def _iterate(self) -> AsyncGenerator[AntigravityStreamChunk, None]:
        assert self.process.stdout is not None
        try:
            while True:
                line_bytes = await asyncio.wait_for(
                    self.process.stdout.readline(),
                    timeout=self.timeout,
                )
                if not line_bytes:
                    break

                line_str = line_bytes.decode("utf-8", errors="replace").strip()
                if not line_str:
                    continue

                try:
                    payload = json.loads(line_str)
                except Exception:
                    continue

                event = payload.get("event")
                if event == "step_update":
                    step = payload.get("step_update", {})
                    if step.get("step_type") == "agent_response":
                        delta = step.get("text_delta")
                        if delta:
                            yield AntigravityStreamChunk(delta)
                        usage = step.get("usage")
                        if usage:
                            self.prompt_tokens = usage.get("input_tokens")
                            self.completion_tokens = usage.get("output_tokens")
                            self.total_tokens = usage.get("total_tokens")

                elif event == "result":
                    res = payload.get("result", {})
                    self.status = res.get("status")
                    usage = res.get("usage")
                    if usage:
                        self.prompt_tokens = usage.get("input_tokens")
                        self.completion_tokens = usage.get("output_tokens")
                        self.total_tokens = usage.get("total_tokens")

            await self.process.wait()
            if self.process.returncode != 0:
                stderr = ""
                if self.process.stderr:
                    err_bytes = await self.process.stderr.read()
                    stderr = err_bytes.decode("utf-8", errors="replace").strip()
                logger.error("agy exited with code %s: %s", self.process.returncode, stderr)
                if not self.status:
                    raise LLMError(f"Antigravity CLI failed with code {self.process.returncode}: {stderr}")

        except asyncio.TimeoutError as exc:
            try:
                self.process.kill()
            except Exception:
                pass
            raise LLMTimeoutError(f"Antigravity CLI timed out after {self.timeout}s") from exc
        except LLMError:
            raise
        except Exception as exc:
            try:
                self.process.kill()
            except Exception:
                pass
            raise LLMError(f"Antigravity stream error: {exc}") from exc


class AntigravityLLMClient:
    """Invokes Antigravity CLI (agy) as an LLM provider."""

    def __init__(
        self,
        binary_path: str = "/home/dan/.local/bin/agy",
        model: str | None = None,
        effort: str = "",
    ) -> None:
        self.binary_path = binary_path
        self.model = model
        self.effort = effort

    def _format_prompt(self, messages: list[dict[str, Any]]) -> str:
        """Format a list of chat messages into a coherent prompt for agy."""
        system_prompts: list[str] = []
        conversation: list[str] = []

        for msg in messages:
            role = msg.get("role", "user").lower()
            content = msg.get("content", "")
            if not isinstance(content, str):
                content = str(content)

            if role == "system":
                system_prompts.append(content)
            elif role == "assistant":
                conversation.append(f"Assistant: {content}")
            else:
                conversation.append(f"User: {content}")

        parts: list[str] = []
        if system_prompts:
            parts.append("[System Instructions]\n" + "\n\n".join(system_prompts))

        if conversation:
            if len(conversation) == 1 and not system_prompts:
                # Simple single-turn prompt
                return conversation[0].removeprefix("User: ")
            parts.append("[Conversation]\n" + "\n\n".join(conversation))

        return "\n\n".join(parts)

    async def do_chat(
        self,
        messages: list[dict[str, Any]],
        stream: bool = False,
        request_timeout: float = 120.0,
    ) -> str | AntigravityStream:
        prompt = self._format_prompt(messages)

        cmd = [
            self.binary_path,
            "-p",
            prompt,
            "--output-format",
            "stream-json",
            "--disable-slash-commands",
        ]

        if self.model:
            cmd.extend(["--model", self.model])

        model_has_effort = bool(
            self.model
            and any(
                self.model.endswith(f"-{e}")
                for e in ("low", "medium", "high", "xhigh", "max")
            )
        )
        if not model_has_effort and self.effort in (
            "low",
            "medium",
            "high",
            "xhigh",
            "max",
        ):
            cmd.extend(["--effort", self.effort])

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise LLMUnavailableError(
                f"Antigravity CLI binary not found at {self.binary_path}."
            ) from exc
        except Exception as exc:
            raise LLMUnavailableError(f"Failed to launch Antigravity CLI: {exc}") from exc

        stream_wrapper = AntigravityStream(process, timeout=request_timeout)

        if stream:
            return stream_wrapper

        # Non-streaming mode: collect all tokens
        collected: list[str] = []
        async for chunk in stream_wrapper:
            collected.append(chunk._content)

        full_content = "".join(collected).strip()
        if not full_content:
            raise LLMResponseError("Antigravity CLI returned an empty response")

        return full_content
