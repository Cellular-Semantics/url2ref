"""Agent connection module using LiteLLM for unified API access."""

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

import litellm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AgentConnection(ABC):
    """Abstract base class for agent connections."""

    def __init__(self, model: str, api_key: Optional[str] = None):
        """Initialize agent connection.

        Args:
            model: Model identifier (e.g., 'gpt-3.5-turbo', 'claude-3-haiku-20240307')
            api_key: API key for the service (optional, can use env vars)

        Raises:
            ValueError: If model is None or empty
        """
        if not model:
            raise ValueError("Model is required")
        self.model = model
        self.api_key = api_key

    @abstractmethod
    def query(self, prompt: str) -> str:
        """Query the agent with a prompt.

        Args:
            prompt: The prompt to send to the agent

        Returns:
            The agent's response
        """
        pass


class LiteLLMAgent(AgentConnection):
    """Agent implementation using LiteLLM for unified API access."""

    def __init__(self, model: str, api_key: Optional[str] = None, max_tokens: int = 150):
        """Initialize LiteLLM agent.

        Args:
            model: Model identifier (e.g., 'gpt-3.5-turbo', 'claude-3-haiku-20240307')
            api_key: API key (optional, will use environment variables)
            max_tokens: Maximum tokens for response
        """
        super().__init__(model, api_key)
        self.max_tokens = max_tokens

    def query(self, prompt: str) -> str:
        """Query LLM using LiteLLM with unified interface.

        Args:
            prompt: The prompt to send

        Returns:
            The model's response

        Raises:
            Exception: If API request fails
        """
        try:
            # Prepare completion parameters
            completion_params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": self.max_tokens
            }

            # Add API key if provided (LiteLLM will use env vars otherwise)
            if self.api_key:
                completion_params["api_key"] = self.api_key

            response = litellm.completion(**completion_params)
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Failed to query {self.model}: {str(e)}")


# Convenience classes for backward compatibility
class OpenAIAgent(LiteLLMAgent):
    """OpenAI agent implementation using LiteLLM."""

    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """Initialize OpenAI agent.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-3.5-turbo)
        """
        if not api_key:
            raise ValueError("API key is required")
        super().__init__(model=model, api_key=api_key)


class AnthropicAgent(LiteLLMAgent):
    """Anthropic agent implementation using LiteLLM."""

    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        """Initialize Anthropic agent.

        Args:
            api_key: Anthropic API key
            model: Model to use (default: claude-3-haiku-20240307)
        """
        if not api_key:
            raise ValueError("API key is required")
        super().__init__(model=model, api_key=api_key)


def create_agent_from_env(provider: str, model: Optional[str] = None) -> AgentConnection:
    """Create an agent from environment variables.

    Args:
        provider: Either 'openai', 'anthropic', or model name directly
        model: Optional model override

    Returns:
        Configured agent instance

    Raises:
        ValueError: If provider is unsupported or API key not found
    """
    if provider.lower() == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        model_name = model or "gpt-3.5-turbo"
        return OpenAIAgent(api_key, model_name)
    elif provider.lower() == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        model_name = model or "claude-3-haiku-20240307"
        return AnthropicAgent(api_key, model_name)
    else:
        # Check if it looks like a valid model name
        valid_prefixes = ['gpt', 'claude', 'gemini', 'llama', 'mistral', 'command']
        if any(provider.lower().startswith(prefix) for prefix in valid_prefixes):
            return LiteLLMAgent(model=provider)
        else:
            raise ValueError(f"Unsupported provider: {provider}")