#!/usr/bin/env python3
"""
Groq-based LLM helper for generating and analyzing Google dorks.

This module integrates the Groq Chat Completions API and exposes
small helper methods that the rest of the toolkit can call to:

- Generate dorks from a natural-language description
- Explain what a given dork does and what it can find
- Suggest related / refined dorks for the same target
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from groq import Groq

# Default model can be overridden via environment
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "moonshotai/kimi-k2-instruct-0905")


class GroqDorkAssistant:
    """Small wrapper around Groq Chat Completions focused on dorking use cases."""

    def __init__(self,
                 model: Optional[str] = None,
                 temperature: float = 0.4,
                 max_tokens: int = 512) -> None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY no está configurada en el entorno (.env).")

        # The Groq client picks the key from the argument or the environment.
        self.client = Groq(api_key=api_key)
        self.model = model or DEFAULT_GROQ_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens

    # ----------------------------
    # Low-level chat helper
    # ----------------------------
    def _chat(self,
              messages: List[Dict[str, str]],
              stream: bool = False,
              max_tokens: Optional[int] = None,
              temperature: Optional[float] = None) -> str:
        """Call Groq chat.completions and optionally stream to stdout.

        Returns the full assistant text as a single string.
        """
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature if temperature is not None else self.temperature,
            max_completion_tokens=max_tokens if max_tokens is not None else self.max_tokens,
            top_p=1.0,
            stream=stream,
        )

        if stream:
            chunks: List[str] = []
            for chunk in completion:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    print(delta, end="", flush=True)
                    chunks.append(delta)
            print()  # newline after streaming
            return "".join(chunks).strip()

        # Non-streaming response
        try:
            text = completion.choices[0].message.content or ""
        except Exception:  # pragma: no cover - very defensive
            text = ""
        return text.strip()

    # ----------------------------
    # Public high-level methods
    # ----------------------------
    def generate_dorks_from_prompt(self,
                                  prompt: str,
                                  engine: str = "google",
                                  stream: bool = True) -> str:
        """Generate one or more dorks from a natural-language description.

        Args:
            prompt: Descripción en lenguaje natural de lo que quieres encontrar.
            engine: "google" o "duckduckgo" (solo afecta a las sugerencias).
            stream: Si True, escribe la respuesta en tiempo real por stdout.

        Returns:
            Texto completo devuelto por el modelo (uno o varios dorks).
        """
        engine = (engine or "google").lower().strip()
        if engine not in {"google", "duckduckgo"}:
            engine = "google"

        system_msg = (
            "Eres un experto en Google dorking y OSINT. "
            "A partir de una descripción en lenguaje natural debes proponer "
            "entre 1 y 5 dorks concretos, optimizados para motores de búsqueda. "
            "Si el usuario indica 'duckduckgo', evita operadores que no soporte "
            "y simplifica la sintaxis. Responde en ESPAÑOL, en texto plano, "
            "UN dork por línea, sin explicaciones adicionales."
        )

        user_msg = (
            f"Motor preferido: {engine}\n"
            f"Descripción del objetivo: {prompt}\n\n"
            "Responde SOLO con los dorks, sin ningún comentario extra."
        )

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]
        return self._chat(messages, stream=stream)

    def explain_dork(self, dork: str, stream: bool = True) -> str:
        """Explain what a dork does, what it tends to find and risk level."""
        system_msg = (
            "Eres un analista de seguridad experto en Google dorking. "
            "Explica de forma breve y clara QUÉ intenta encontrar el dork, "
            "qué tipo de activos o datos suelen aparecer y qué nivel de riesgo "
            "puede implicar para un objetivo. Responde en ESPAÑOL."
        )
        user_msg = f"Dork a analizar:\n{dork}"
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]
        return self._chat(messages, stream=stream, max_tokens=512)

    def suggest_related_dorks(self, dork: str, stream: bool = True) -> str:
        """Suggest related/refined dorks starting from an existing one."""
        system_msg = (
            "Eres un generador de dorks avanzado. A partir de un dork existente, "
            "propón variantes que: (1) afinen la búsqueda, (2) amplíen el alcance "
            "o (3) se centren en otros vectores relacionados (por ejemplo, backups, "
            "subdominios, paneles de login, etc.). Responde en ESPAÑOL y devuelve "
            "SOLO la lista de dorks, un dork por línea, sin comentarios."
        )
        user_msg = (
            "Dork base:\n"
            f"{dork}\n\n"
            "Genera entre 3 y 7 dorks relacionados."
        )
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]
        return self._chat(messages, stream=stream, max_tokens=512)


def demo():
    """Pequeña demo en línea de comandos para probar rápidamente el asistente."""
    assistant = GroqDorkAssistant()
    print("\n🤖 Asistente LLM de dorks (Groq)")
    print("=" * 60)
    while True:
        prompt = input("\nDescribe qué quieres encontrar (o Enter para salir): ").strip()
        if not prompt:
            break
        engine = input("Motor (google/duckduckgo, Enter=google): ").strip() or "google"
        print("\nDorks sugeridos:\n")
        assistant.generate_dorks_from_prompt(prompt, engine=engine, stream=True)


if __name__ == "__main__":
    demo()