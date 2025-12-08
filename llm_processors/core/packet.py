"""
Packet: The standard data object for content processing.

A Packet represents a single piece of content of a given modality (text, image, bytes)
with associated metadata for routing and categorization.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore


# Type aliases
PacketTypes = Union[str, bytes, 'Image.Image', 'Packet']


@dataclass(frozen=True)
class Packet:
    """
    Standard data object representing a single piece of content.

    A Packet represents content of a specific modality (text, image, bytes)
    with associated metadata for routing and categorization.

    Attributes:
        content: The actual content (str, bytes, or PIL.Image.Image)
        metadata: Dictionary of metadata for routing and categorization

    Examples:
        >>> packet = Packet.from_text("Hello, world!")
        >>> packet.is_text()
        True
        >>> packet.mimetype
        'text/plain'

        >>> packet = packet.with_metadata(author="Alice")
        >>> packet.metadata['author']
        'Alice'
    """
    content: Union[str, bytes, 'Image.Image']
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def mimetype(self) -> Optional[str]:
        """Get MIME type from metadata."""
        return self.metadata.get('mimetype')

    @property
    def substream_name(self) -> Optional[str]:
        """Get substream name from metadata."""
        return self.metadata.get('substream_name')

    def with_metadata(self, **kwargs: Any) -> 'Packet':
        """
        Create new Packet with updated metadata (immutable update).

        Args:
            **kwargs: Metadata key-value pairs to add/update

        Returns:
            New Packet instance with merged metadata

        Examples:
            >>> packet = Packet.from_text("Hello")
            >>> new_packet = packet.with_metadata(source="user", priority=1)
            >>> new_packet.metadata['source']
            'user'
        """
        new_metadata = {**self.metadata, **kwargs}
        return Packet(content=self.content, metadata=new_metadata)

    def is_text(self) -> bool:
        """Check if content is text."""
        return isinstance(self.content, str)

    def is_bytes(self) -> bool:
        """Check if content is bytes."""
        return isinstance(self.content, bytes)

    def is_image(self) -> bool:
        """Check if content is PIL Image."""
        if Image is None:
            return False
        return isinstance(self.content, Image.Image)

    @classmethod
    def from_text(cls, text: str, **metadata: Any) -> 'Packet':
        """
        Convenience constructor for text packets.

        Args:
            text: Text content
            **metadata: Additional metadata

        Returns:
            Packet with text content and text/plain mimetype

        Examples:
            >>> packet = Packet.from_text("Hello", author="Alice")
            >>> packet.content
            'Hello'
            >>> packet.mimetype
            'text/plain'
        """
        return cls(content=text, metadata={'mimetype': 'text/plain', **metadata})

    @classmethod
    def from_bytes(cls, data: bytes, mimetype: str = 'application/octet-stream', **metadata: Any) -> 'Packet':
        """
        Convenience constructor for bytes packets.

        Args:
            data: Bytes content
            mimetype: MIME type of the bytes content
            **metadata: Additional metadata

        Returns:
            Packet with bytes content and specified mimetype

        Examples:
            >>> packet = Packet.from_bytes(b"binary data", mimetype="application/pdf")
            >>> packet.is_bytes()
            True
            >>> packet.mimetype
            'application/pdf'
        """
        return cls(content=data, metadata={'mimetype': mimetype, **metadata})

    @classmethod
    def from_image(cls, image: 'Image.Image', mimetype: str = 'image/png', **metadata: Any) -> 'Packet':
        """
        Convenience constructor for image packets.

        Args:
            image: PIL Image object
            mimetype: MIME type of the image
            **metadata: Additional metadata

        Returns:
            Packet with image content and specified mimetype

        Examples:
            >>> from PIL import Image
            >>> img = Image.new('RGB', (100, 100))
            >>> packet = Packet.from_image(img)
            >>> packet.is_image()
            True
            >>> packet.mimetype
            'image/png'
        """
        if Image is None:
            raise ImportError("PIL/Pillow is required for image support. Install with: pip install Pillow")
        return cls(content=image, metadata={'mimetype': mimetype, **metadata})

    def __repr__(self) -> str:
        """String representation of Packet."""
        content_type = "text" if self.is_text() else "bytes" if self.is_bytes() else "image"
        content_preview = ""

        if self.is_text():
            preview = self.content[:50]  # type: ignore
            content_preview = f'"{preview}..."' if len(self.content) > 50 else f'"{self.content}"'  # type: ignore
        elif self.is_bytes():
            content_preview = f"{len(self.content)} bytes"  # type: ignore
        elif self.is_image():
            content_preview = f"{self.content.size}"  # type: ignore

        metadata_str = f", {len(self.metadata)} metadata" if self.metadata else ""
        return f"Packet({content_type}: {content_preview}{metadata_str})"
