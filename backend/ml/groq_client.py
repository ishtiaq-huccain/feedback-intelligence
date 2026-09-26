import os
from typing import List, Dict, Optional, Generator, Union
from groq import Groq
from backend.config import get_settings

settings = get_settings()


class GroqClient:
    """
    Wrapper around Groq API to standardize LLM calls.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.groq_api_key
        self.model = model or settings.groq_model
        self.client = Groq(api_key=self.api_key)

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 512,
        stream: bool = False,
    ) -> Union[str, Generator[str, None, None]]:
        """
        Send chat messages to Groq model.
        - If stream=False → returns a single string
        - If stream=True → returns a generator of tokens
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )

        if stream:
            def _stream_gen() -> Generator[str, None, None]:
                output = ""
                for chunk in response:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        output += delta
                        yield delta
            return _stream_gen()
        else:
            return response.choices[0].message.content or ""


# ✅ Global singleton
groq_client = GroqClient()
