"""
Tests for Packet class.
"""

import pytest
from llm_processors import Packet


@pytest.mark.unit
def test_packet_creation():
    """Test basic packet creation."""
    packet = Packet.from_text("test content")
    assert packet.content == "test content"
    assert packet.mimetype == "text/plain"


@pytest.mark.unit
def test_packet_with_metadata():
    """Test packet creation with metadata."""
    packet = Packet.from_text("test", author="Alice", priority=1)
    assert packet.content == "test"
    assert packet.metadata["author"] == "Alice"
    assert packet.metadata["priority"] == 1


@pytest.mark.unit
def test_packet_immutability():
    """Test that packets are immutable."""
    packet = Packet.from_text("test")
    new_packet = packet.with_metadata(new_key="value")

    # Original unchanged
    assert "new_key" not in packet.metadata

    # New packet has the metadata
    assert new_packet.metadata["new_key"] == "value"
    assert new_packet.content == packet.content


@pytest.mark.unit
def test_packet_type_predicates():
    """Test type checking methods."""
    text_packet = Packet.from_text("hello")
    assert text_packet.is_text()
    assert not text_packet.is_bytes()
    assert not text_packet.is_image()

    bytes_packet = Packet.from_bytes(b"binary")
    assert bytes_packet.is_bytes()
    assert not bytes_packet.is_text()
    assert not bytes_packet.is_image()


@pytest.mark.unit
def test_packet_from_bytes():
    """Test bytes packet creation."""
    data = b"binary data"
    packet = Packet.from_bytes(data, mimetype="application/pdf")

    assert packet.content == data
    assert packet.mimetype == "application/pdf"
    assert packet.is_bytes()


@pytest.mark.unit
def test_packet_properties():
    """Test packet properties."""
    packet = Packet.from_text("test")

    assert packet.mimetype == "text/plain"
    assert packet.substream_name is None

    packet = packet.with_metadata(substream_name="branch_1")
    assert packet.substream_name == "branch_1"


@pytest.mark.unit
def test_packet_repr():
    """Test packet string representation."""
    packet = Packet.from_text("Hello, world!")
    repr_str = repr(packet)

    assert "Packet" in repr_str
    assert "text" in repr_str
    assert "Hello, world!" in repr_str


@pytest.mark.unit
def test_packet_with_metadata_chaining():
    """Test chaining multiple with_metadata calls."""
    packet = Packet.from_text("test")
    packet = (packet
              .with_metadata(author="Alice")
              .with_metadata(priority=1)
              .with_metadata(tags=["important"]))

    assert packet.metadata["author"] == "Alice"
    assert packet.metadata["priority"] == 1
    assert packet.metadata["tags"] == ["important"]
