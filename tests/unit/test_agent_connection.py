"""Unit tests for agent connection module."""

import pytest
from unittest.mock import Mock, patch
from lit_agent.agent_connection import (
    AgentConnection,
    OpenAIAgent,
    AnthropicAgent,
    LiteLLMAgent,
)


@pytest.mark.unit
class TestAgentConnection:
    """Test the base AgentConnection class."""

    def test_agent_connection_is_abstract(self):
        """Test that AgentConnection cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AgentConnection("test-model")

    def test_agent_connection_requires_model(self):
        """Test that concrete agents require a model."""
        with pytest.raises(ValueError, match="Model is required"):
            LiteLLMAgent(model=None)

        with pytest.raises(ValueError, match="Model is required"):
            LiteLLMAgent(model="")


@pytest.mark.unit
class TestLiteLLMAgent:
    """Test the LiteLLM agent implementation."""

    def test_litellm_agent_initialization(self):
        """Test LiteLLM agent can be initialized with valid model."""
        agent = LiteLLMAgent(model="gpt-3.5-turbo")
        assert agent.model == "gpt-3.5-turbo"
        assert agent.api_key is None  # not required
        assert agent.max_tokens == 150  # default

    def test_litellm_agent_with_api_key(self):
        """Test LiteLLM agent can be initialized with API key."""
        agent = LiteLLMAgent(model="gpt-4", api_key="test-key", max_tokens=300)
        assert agent.model == "gpt-4"
        assert agent.api_key == "test-key"
        assert agent.max_tokens == 300

    @patch("litellm.completion")
    def test_litellm_agent_query(self, mock_completion):
        """Test LiteLLM agent can make queries."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Hello world example response"
        mock_completion.return_value = mock_response

        agent = LiteLLMAgent(model="gpt-3.5-turbo")
        response = agent.query("Hello world coding example")

        assert response == "Hello world example response"
        mock_completion.assert_called_once_with(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello world coding example"}],
            max_tokens=150,
        )

    @patch("litellm.completion")
    def test_litellm_agent_query_error(self, mock_completion):
        """Test LiteLLM agent handles query errors."""
        mock_completion.side_effect = Exception("API Error")

        agent = LiteLLMAgent(model="gpt-3.5-turbo")

        with pytest.raises(Exception, match="Failed to query gpt-3.5-turbo: API Error"):
            agent.query("test prompt")


@pytest.mark.unit
class TestOpenAIAgent:
    """Test the OpenAI agent implementation."""

    def test_openai_agent_initialization(self):
        """Test OpenAI agent can be initialized with valid API key."""
        agent = OpenAIAgent(api_key="test-key")
        assert agent.api_key == "test-key"
        assert agent.model == "gpt-3.5-turbo"  # default model

    def test_openai_agent_custom_model(self):
        """Test OpenAI agent can use custom model."""
        agent = OpenAIAgent(api_key="test-key", model="gpt-4")
        assert agent.model == "gpt-4"

    def test_openai_agent_requires_api_key(self):
        """Test that OpenAI agent requires an API key."""
        with pytest.raises(ValueError, match="API key is required"):
            OpenAIAgent(api_key=None)

        with pytest.raises(ValueError, match="API key is required"):
            OpenAIAgent(api_key="")

    @patch("litellm.completion")
    def test_openai_agent_query(self, mock_completion):
        """Test OpenAI agent can make queries via LiteLLM."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Hello world example response"
        mock_completion.return_value = mock_response

        agent = OpenAIAgent(api_key="test-key")
        response = agent.query("Hello world coding example")

        assert response == "Hello world example response"
        mock_completion.assert_called_once()


@pytest.mark.unit
class TestAnthropicAgent:
    """Test the Anthropic agent implementation."""

    def test_anthropic_agent_initialization(self):
        """Test Anthropic agent can be initialized with valid API key."""
        agent = AnthropicAgent(api_key="test-key")
        assert agent.api_key == "test-key"
        assert agent.model == "claude-3-haiku-20240307"  # default model

    def test_anthropic_agent_custom_model(self):
        """Test Anthropic agent can use custom model."""
        agent = AnthropicAgent(api_key="test-key", model="claude-3-opus-20240229")
        assert agent.model == "claude-3-opus-20240229"

    def test_anthropic_agent_requires_api_key(self):
        """Test that Anthropic agent requires an API key."""
        with pytest.raises(ValueError, match="API key is required"):
            AnthropicAgent(api_key=None)

        with pytest.raises(ValueError, match="API key is required"):
            AnthropicAgent(api_key="")

    @patch("litellm.completion")
    def test_anthropic_agent_query(self, mock_completion):
        """Test Anthropic agent can make queries via LiteLLM."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Hello world example response"
        mock_completion.return_value = mock_response

        agent = AnthropicAgent(api_key="test-key")
        response = agent.query("Hello world coding example")

        assert response == "Hello world example response"
        mock_completion.assert_called_once()


@pytest.mark.unit
class TestAgentFactory:
    """Test the agent factory functionality."""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-openai-key"})
    def test_create_openai_agent_from_env(self):
        """Test creating OpenAI agent from environment variables."""
        from lit_agent.agent_connection import create_agent_from_env

        agent = create_agent_from_env("openai")
        assert isinstance(agent, OpenAIAgent)
        assert agent.api_key == "test-openai-key"

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-anthropic-key"})
    def test_create_anthropic_agent_from_env(self):
        """Test creating Anthropic agent from environment variables."""
        from lit_agent.agent_connection import create_agent_from_env

        agent = create_agent_from_env("anthropic")
        assert isinstance(agent, AnthropicAgent)
        assert agent.api_key == "test-anthropic-key"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-openai-key"})
    def test_create_agent_with_custom_model(self):
        """Test creating agent with custom model."""
        from lit_agent.agent_connection import create_agent_from_env

        agent = create_agent_from_env("openai", model="gpt-4")
        assert isinstance(agent, OpenAIAgent)
        assert agent.model == "gpt-4"

    def test_create_agent_direct_model(self):
        """Test creating agent using model name directly."""
        from lit_agent.agent_connection import create_agent_from_env

        agent = create_agent_from_env("gpt-3.5-turbo")
        assert isinstance(agent, LiteLLMAgent)
        assert agent.model == "gpt-3.5-turbo"

    def test_create_agent_invalid_provider(self):
        """Test creating agent with invalid provider raises error."""
        from lit_agent.agent_connection import create_agent_from_env

        with pytest.raises(ValueError, match="Unsupported provider"):
            create_agent_from_env("invalid")
