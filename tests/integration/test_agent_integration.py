"""Integration tests for agent connections with real API calls."""

import pytest
import os
import warnings
from unittest.mock import Mock, patch
from lit_agent.agent_connection import (
    create_agent_from_env,
    OpenAIAgent,
    AnthropicAgent,
)


@pytest.mark.integration
class TestOpenAIIntegration:
    """Integration tests for OpenAI agent with real API calls."""

    def test_openai_hello_world_query(self):
        """Test OpenAI agent with hello world coding example request."""
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            # Fallback to mock with warning
            warnings.warn(
                "OPENAI_API_KEY not found - falling back to mock test. "
                "Set OPENAI_API_KEY environment variable for real integration testing.",
                UserWarning,
            )

            # Mock test
            with patch("litellm.completion") as mock_completion:
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message = Mock()
                mock_response.choices[0].message.content = (
                    'Here\'s a simple "Hello, World!" program in Python:\n\n'
                    '```python\nprint("Hello, World!")\n```\n\n'
                    'This program uses the print() function to display the text "Hello, World!" to the console. '
                    "It's typically the first program beginners learn when starting with Python."
                )
                mock_completion.return_value = mock_response

                agent = OpenAIAgent("mock-key")
                prompt = "Write a hello world program in Python. Please provide a brief answer in 2-3 sentences."

                response = agent.query(prompt)

                print("\n--- OpenAI Hello World Response (MOCK) ---")
                print(response)
                print("--- End Response ---\n")

                # Verify mock response
                assert isinstance(response, str)
                assert len(response.strip()) > 0
                assert "print" in response.lower() and "hello" in response.lower()
        else:
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
            # Fallback to mock with warning
            warnings.warn(
                "OPENAI_API_KEY not found - falling back to mock test for factory function.",
                UserWarning,
            )

            # Mock the environment and API call
            with patch.dict("os.environ", {"OPENAI_API_KEY": "mock-key"}):
                with patch("litellm.completion") as mock_completion:
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message = Mock()
                    mock_response.choices[0].message.content = "Hello!"
                    mock_completion.return_value = mock_response

                    agent = create_agent_from_env("openai")
                    assert isinstance(agent, OpenAIAgent)

                    # Test a simple query
                    response = agent.query("Say hello in one word.")
                    assert isinstance(response, str)
                    assert len(response.strip()) > 0
        else:
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
            # Fallback to mock with warning
            warnings.warn(
                "ANTHROPIC_API_KEY not found - falling back to mock test. "
                "Set ANTHROPIC_API_KEY environment variable for real integration testing.",
                UserWarning,
            )

            # Mock test
            with patch("litellm.completion") as mock_completion:
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message = Mock()
                mock_response.choices[0].message.content = (
                    "The first recorded use of 'Hello, World!' was by Brian Kernighan in 1972. "
                    "It appeared in 'The C Programming Language' book as a simple example program. "
                    "The program simply prints 'hello, world' to demonstrate basic syntax."
                )
                mock_completion.return_value = mock_response

                agent = AnthropicAgent("mock-key")
                prompt = (
                    "What is the first recorded use of Hello World to demonstrate "
                    "a programming language. Please provide a brief answer in 2-3 sentences."
                )

                response = agent.query(prompt)

                print("\n--- Anthropic Hello World Response (MOCK) ---")
                print(response)
                print("--- End Response ---\n")

                # Verify mock response
                assert isinstance(response, str)
                assert len(response.strip()) > 0
                assert "hello" in response.lower()
        else:
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
            # Fallback to mock with warning
            warnings.warn(
                "ANTHROPIC_API_KEY not found - falling back to mock test for factory function.",
                UserWarning,
            )

            # Mock the environment and API call
            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "mock-key"}):
                with patch("litellm.completion") as mock_completion:
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message = Mock()
                    mock_response.choices[0].message.content = "Hello!"
                    mock_completion.return_value = mock_response

                    agent = create_agent_from_env("anthropic")
                    assert isinstance(agent, AnthropicAgent)

                    # Test a simple query
                    response = agent.query("Say hello in one word.")
                    assert isinstance(response, str)
                    assert len(response.strip()) > 0
        else:
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
            # No real API keys, use mocks with warning
            warnings.warn(
                "No API keys found for OpenAI or Anthropic - falling back to mock tests. "
                "Set OPENAI_API_KEY or ANTHROPIC_API_KEY for real integration testing.",
                UserWarning,
            )

            with patch.dict(
                "os.environ",
                {
                    "OPENAI_API_KEY": "mock-openai-key",
                    "ANTHROPIC_API_KEY": "mock-anthropic-key",
                },
            ):
                with patch("litellm.completion") as mock_completion:
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message = Mock()
                    mock_response.choices[0].message.content = "Hello!"
                    mock_completion.return_value = mock_response

                    # Test both agents with mocks
                    openai_agent = create_agent_from_env("openai")
                    response = openai_agent.query("Hello")
                    assert isinstance(response, str)

                    anthropic_agent = create_agent_from_env("anthropic")
                    response = anthropic_agent.query("Hello")
                    assert isinstance(response, str)
        else:
            # Real API tests
            if openai_available:
                agent = create_agent_from_env("openai")
                response = agent.query("Hello")
                assert isinstance(response, str)

            if anthropic_available:
                agent = create_agent_from_env("anthropic")
                response = agent.query("Hello")
                assert isinstance(response, str)
