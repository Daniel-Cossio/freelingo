import asyncio
import os
import sys

# Ensure backend is on PYTHONPATH
sys.path.insert(0, os.path.abspath("backend"))

from app.core.config import settings
from app.services.llm_adapter import LLMAdapter, parse_llm_json
from app.services.llm_antigravity import AntigravityLLMClient


async def test_antigravity_client():
    print("=== Test 1: Direct AntigravityLLMClient (Non-streaming) ===")
    client = AntigravityLLMClient(
        binary_path=settings.ANTIGRAVITY_BIN_PATH,
        model=settings.ANTIGRAVITY_MODEL,
        effort=settings.ANTIGRAVITY_EFFORT,
    )
    prompt_messages = [
        {"role": "system", "content": "You are a concise language tutor. Answer in Spanish."},
        {"role": "user", "content": "Di 'Bienvenido a FreeLingo con Antigravity' en una sola frase corta."},
    ]
    response = await client.do_chat(prompt_messages, stream=False)
    print("Respuesta recibida:\n", response)
    assert len(response) > 5, "Response too short"
    print("-> Test 1 PASSED!\n")

    print("=== Test 2: Direct AntigravityLLMClient (Streaming) ===")
    stream = await client.do_chat(
        [{"role": "user", "content": "Cuenta del 1 al 5 en inglés separados por comas."}],
        stream=True,
    )
    collected = []
    print("Tokens en streaming: ", end="", flush=True)
    async for chunk in stream:
        token = str(chunk)
        print(token, end="", flush=True)
        collected.append(token)
    print("\nTokens recibidos:", len(collected))
    print("Uso de tokens:", getattr(stream, "total_tokens", None))
    assert len(collected) > 0, "No stream chunks received"
    print("-> Test 2 PASSED!\n")

    print("=== Test 3: LLMAdapter with provider='antigravity' ===")
    settings.LLM_PROVIDER = "antigravity"
    adapter = LLMAdapter()
    res = await adapter.chat(
        [
            {
                "role": "system",
                "content": "Return a JSON object with keys 'language' and 'level'. No markdown fences.",
            },
            {"role": "user", "content": "Language: English, Level: A1"},
        ],
        stream=False,
    )
    print("JSON generado:", res)
    parsed = parse_llm_json(res)
    print("Parsed JSON:", parsed)
    assert "language" in parsed or "level" in parsed, "Invalid JSON structure"
    print("-> Test 3 PASSED!\n")

    print("=== ALL ADAPTER TESTS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    asyncio.run(test_antigravity_client())
