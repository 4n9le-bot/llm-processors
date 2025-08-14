from unittest.mock import patch, Mock
from llm_processors.processors.chat_processor import ChatProcessor


class TestChatProcessor:
    """Test cases for ChatProcessor with kwargs refactoring"""

    @patch('llm_processors.processors.chat_processor.OpenAI')
    def test_init_with_defaults(self, mock_openai):
        """Test ChatProcessor initialization with default kwargs values"""
        mock_openai.return_value = Mock()
        
        processor = ChatProcessor()
        
        assert processor.temperature == 0.6
        assert processor.max_tokens is None
        assert processor.response_format == "text"
        assert processor.model == "gpt-4o-mini"

    @patch('llm_processors.processors.chat_processor.OpenAI')
    def test_init_with_kwargs(self, mock_openai):
        """Test ChatProcessor initialization with custom kwargs values"""
        mock_openai.return_value = Mock()
        
        processor = ChatProcessor(
            temperature=0.8,
            max_tokens=1000,
            response_format="json"
        )
        
        assert processor.temperature == 0.8
        assert processor.max_tokens == 1000
        assert processor.response_format == "json"

    @patch('llm_processors.processors.chat_processor.OpenAI')
    def test_init_with_mixed_args_and_kwargs(self, mock_openai):
        """Test ChatProcessor initialization with both positional and kwargs"""
        mock_openai.return_value = Mock()
        
        processor = ChatProcessor(
            model="gpt-4",
            name="test_processor",
            temperature=0.9,
            max_tokens=2000
        )
        
        assert processor.model == "gpt-4"
        assert processor.name == "test_processor"
        assert processor.temperature == 0.9
        assert processor.max_tokens == 2000
        assert processor.response_format == "text"  # default value

    @patch('llm_processors.processors.chat_processor.OpenAI')
    def test_backward_compatibility(self, mock_openai):
        """Test that the refactoring maintains backward compatibility"""
        mock_openai.return_value = Mock()
        
        # Test all different ways to initialize
        
        # 1. No optional params
        p1 = ChatProcessor()
        assert p1.temperature == 0.6
        
        # 2. Only some kwargs
        p2 = ChatProcessor(temperature=0.5)
        assert p2.temperature == 0.5
        assert p2.max_tokens is None
        
        # 3. All kwargs
        p3 = ChatProcessor(
            temperature=0.7,
            max_tokens=500,
            response_format="json"
        )
        assert p3.temperature == 0.7
        assert p3.max_tokens == 500
        assert p3.response_format == "json"

    @patch('llm_processors.processors.chat_processor.OpenAI')
    def test_invalid_kwargs_ignored(self, mock_openai):
        """Test that invalid kwargs are ignored gracefully"""
        mock_openai.return_value = Mock()
        
        processor = ChatProcessor(
            temperature=0.5,
            invalid_param="should_be_ignored",
            another_invalid=123
        )
        
        assert processor.temperature == 0.5
        assert processor.max_tokens is None
        assert processor.response_format == "text"
        # Invalid params should not cause errors
