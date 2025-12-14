"""Integration tests for agent connections with real API calls."""

# Load environment variables first (following CLAUDE.md requirements)
from dotenv import load_dotenv

load_dotenv()

import pytest  # noqa: E402
import os  # noqa: E402

from lit_agent.agent_connection import (  # noqa: E402
    create_agent_from_env,
    OpenAIAgent,
    AnthropicAgent,
)

ALLOW_INTEGRATION_FALLBACK = os.getenv("ALLOW_INTEGRATION_FALLBACK", "").lower() in {
    "1",
    "true",
    "yes",
}


@pytest.mark.integration
class TestOpenAIIntegration:
    """Integration tests for OpenAI agent with real API calls."""

    def test_openai_hello_world_query(self):
        """Test OpenAI agent with hello world coding example request."""
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            if ALLOW_INTEGRATION_FALLBACK:
                pytest.skip("OPENAI_API_KEY not set (allowed fallback)")
            pytest.fail(
                "OPENAI_API_KEY not found; set it or ALLOW_INTEGRATION_FALLBACK=1 to skip"
            )

        # Real API test
        agent = OpenAIAgent(api_key)
        prompt = "Write a hello world program in Python. Please provide a brief answer in 2-3 sentences."

        response = agent.query(prompt)

        print("\n--- OpenAI Hello World Response (REAL API) ---")
        print(response)
        print("--- End Response ---\n")

        # Verify we got a meaningful response
        assert isinstance(response, str)
        assert len(response.strip()) > 0
        assert "print" in response.lower() or "hello" in response.lower()

    def test_openai_agent_from_env(self):
        """Test creating OpenAI agent from environment variables."""
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            if ALLOW_INTEGRATION_FALLBACK:
                pytest.skip("OPENAI_API_KEY not set (allowed fallback)")
            pytest.fail(
                "OPENAI_API_KEY not found; set it or ALLOW_INTEGRATION_FALLBACK=1 to skip"
            )

        # Real API test
        agent = create_agent_from_env("openai")
        assert isinstance(agent, OpenAIAgent)

        # Test a simple query
        response = agent.query("Say hello in one word.")
        assert isinstance(response, str)
        assert len(response.strip()) > 0


@pytest.mark.integration
class TestAnthropicIntegration:
    """Integration tests for Anthropic agent with real API calls."""

    def test_anthropic_hello_world_query(self):
        """Test Anthropic agent with hello world coding example request."""
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            if ALLOW_INTEGRATION_FALLBACK:
                pytest.skip("ANTHROPIC_API_KEY not set (allowed fallback)")
            pytest.fail(
                "ANTHROPIC_API_KEY not found; set it or ALLOW_INTEGRATION_FALLBACK=1 to skip"
            )

        # Real API test
        agent = AnthropicAgent(api_key)
        prompt = (
            "What is the first recorded use of Hello World to demonstrate "
            "a programming language. Please provide a brief answer in 2-3 sentences."
        )

        response = agent.query(prompt)

        # Print the response for verification
        print("\n--- Anthropic Hello World Response (REAL API) ---")
        print(response)
        print("--- End Response ---\n")

        # Verify we got a meaningful response
        assert isinstance(response, str)
        assert len(response.strip()) > 0
        assert (
            "hello" in response.lower()
            or "kernighan" in response.lower()
            or "programming" in response.lower()
        )

    def test_anthropic_agent_from_env(self):
        """Test creating Anthropic agent from environment variables."""
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            if ALLOW_INTEGRATION_FALLBACK:
                pytest.skip("ANTHROPIC_API_KEY not set (allowed fallback)")
            pytest.fail(
                "ANTHROPIC_API_KEY not found; set it or ALLOW_INTEGRATION_FALLBACK=1 to skip"
            )

        # Real API test
        agent = create_agent_from_env("anthropic")
        assert isinstance(agent, AnthropicAgent)

        # Test a simple query
        response = agent.query("Say hello in one word.")
        assert isinstance(response, str)
        assert len(response.strip()) > 0


@pytest.mark.integration
class TestAgentFactoryIntegration:
    """Integration tests for agent factory with real environment."""

    def test_both_agents_available(self):
        """Test that both agent types can be created if keys are available."""
        openai_available = bool(os.getenv("OPENAI_API_KEY"))
        anthropic_available = bool(os.getenv("ANTHROPIC_API_KEY"))

        if not (openai_available or anthropic_available):
            if ALLOW_INTEGRATION_FALLBACK:
                pytest.skip("No API keys found (allowed fallback)")
            pytest.fail(
                "No API keys found for OpenAI or Anthropic; set keys or ALLOW_INTEGRATION_FALLBACK=1 to skip"
            )

        # Real API tests
        if openai_available:
            agent = create_agent_from_env("openai")
            response = agent.query("Hello")
            assert isinstance(response, str)

        if anthropic_available:
            agent = create_agent_from_env("anthropic")
            response = agent.query("Hello")
            assert isinstance(response, str)
