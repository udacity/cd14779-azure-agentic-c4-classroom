
import json
from typing import Optional, Any

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
    AzureChatCompletion,
)

class SKWrapper:
    """
    Strict SK wrapper for semantic-kernel==0.9.6b1.
    Requires a real API key (no demo fallback).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        model: str = "gpt-4o-mini",
        connection_type: str = "openai",
        deployment: Optional[str] = None,
    ):
        if not api_key:
            raise ValueError("api_key is required to initialize SKWrapper")

        self.connection_type = connection_type.lower()
        self.kernel: Optional[Kernel] = None

        try:
            self.kernel = Kernel()

            if self.connection_type == "openai":
                llm = OpenAIChatCompletion(api_key=api_key, model=model)

            elif self.connection_type == "azure":
                azure_deployment = deployment or model
                llm = AzureChatCompletion(
                    api_key=api_key,
                    endpoint=endpoint,
                    deployment_name=azure_deployment,
                )

            else:
                raise ValueError(f"Unsupported connection_type: {connection_type}")

            self.kernel.add_service(llm)
            self._llm_service = llm

        except Exception as e:
            raise RuntimeError(f"Failed to initialize Semantic Kernel and AI service ,cause :{e}") from e

    async def generate_text(self, prompt: str, arguments: Any = None, **gen_kwargs) -> str:
        """
        Invoke the kernel prompt execution and return a string result.
        Accepts generation kwargs forwarded to the underlying LLM (temperature, max_tokens, etc).
        """
        if self.kernel is None:
            raise RuntimeError("Semantic Kernel is not initialized.")

        # semantic-kernel APIs sometimes accept additional kwargs; adjust as needed.
        result = await self.kernel.invoke_prompt(prompt, arguments=arguments, **gen_kwargs)
       
        # Normalization (same as before)
        if result is None:
            return ""
        if isinstance(result, str):
            return result
        if hasattr(result, "text"):
            return getattr(result, "text")
        if hasattr(result, "content"):
            return getattr(result, "content")
        try:
            return str(result)
        except Exception:
            return json.dumps({"unserializable_result": True})