import importlib
import logging
import os
from typing import Optional

import google.generativeai as genai

from embedchain.config import BaseLlmConfig
from embedchain.helpers.json_serializable import register_deserializable
from embedchain.llm.base import BaseLlm


@register_deserializable
class GoogleLlm(BaseLlm):
    def __init__(self, config: Optional[BaseLlmConfig] = None):
        if "GOOGLE_API_KEY" not in os.environ:
            raise ValueError("Please set the GOOGLE_API_KEY environment variable.")

        try:
            importlib.import_module("google.generativeai")
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "The required dependencies for GoogleLlm are not installed."
                'Please install with `pip install --upgrade "embedchain[google]"`'
            ) from None

        super().__init__(config)
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

    def get_llm_model_answer(self, prompt):
        if self.config.system_prompt:
            raise ValueError("GoogleLlm does not support `system_prompt`")
        return GoogleLlm._get_answer(prompt, self.config)

    @staticmethod
    def _get_answer(prompt: str, config: BaseLlmConfig):
        model_name = config.model or "gemini-pro"
        logging.info(f"Using Google LLM model: {model_name}")
        model = genai.GenerativeModel(model_name=model_name)

        generation_config_params = {
            "candidate_count": 1,
            "max_output_tokens": config.max_tokens,
            "temperature": config.temperature or 0.5,
        }

        if config.top_p >= 0.0 and config.top_p <= 1.0:
            generation_config_params["top_p"] = config.top_p
        else:
            raise ValueError("`top_p` must be > 0.0 and < 1.0")

        generation_config = genai.types.GenerationConfig(**generation_config_params)

        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            stream=config.stream,
        )

        if config.stream:
            for chunk in response:
                yield chunk.text
        else:
            return response.text
