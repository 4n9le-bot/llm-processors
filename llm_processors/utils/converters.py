"""
PacketConverter: Utilities for converting between raw types and Packets.

This module provides conversion utilities for transforming raw data types
(str, bytes, PIL.Image) to and from Packet objects.
"""

from typing import Union

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

from llm_processors.core.packet import Packet


class PacketConverter:
    """
    Utility class for converting between raw types and Packets.

    Provides static methods for bidirectional conversion between
    raw data types (str, bytes, PIL.Image) and Packet objects.

    Examples:
        >>> # Convert raw data to Packet
        >>> packet = PacketConverter.to_packet("Hello, world!")
        >>> packet.mimetype
        'text/plain'

        >>> # Convert Packet back to raw data
        >>> data = PacketConverter.from_packet(packet)
        >>> data
        'Hello, world!'
    """

    @staticmethod
    def to_packet(
        data: Union[str, bytes, 'Image.Image'],
        **metadata
    ) -> Packet:
        """
        Convert raw data to Packet with automatic type detection.

        Automatically determines the appropriate MIME type based on
        the input data type and creates a Packet with proper metadata.

        Args:
            data: Raw data (str, bytes, or PIL.Image.Image)
            **metadata: Additional metadata to attach to the Packet

        Returns:
            Packet object with appropriate mimetype and metadata

        Raises:
            TypeError: If data type is not supported
            ImportError: If PIL is required but not installed

        Examples:
            >>> # Text data
            >>> packet = PacketConverter.to_packet("Hello")
            >>> packet.mimetype
            'text/plain'

            >>> # Binary data with custom mimetype
            >>> packet = PacketConverter.to_packet(b"...", mimetype="application/pdf")
            >>> packet.mimetype
            'application/pdf'

            >>> # Image data
            >>> from PIL import Image
            >>> img = Image.new('RGB', (100, 100))
            >>> packet = PacketConverter.to_packet(img)
            >>> packet.is_image()
            True
        """
        if isinstance(data, str):
            return Packet.from_text(data, **metadata)
        elif isinstance(data, bytes):
            # Allow custom mimetype, default to octet-stream
            mimetype = metadata.pop('mimetype', 'application/octet-stream')
            return Packet.from_bytes(data, mimetype=mimetype, **metadata)
        elif Image is not None and isinstance(data, Image.Image):
            # Allow custom mimetype, default to image/png
            mimetype = metadata.pop('mimetype', 'image/png')
            return Packet.from_image(data, mimetype=mimetype, **metadata)
        else:
            raise TypeError(
                f"Unsupported data type: {type(data).__name__}. "
                f"Supported types: str, bytes, PIL.Image.Image"
            )

    @staticmethod
    def from_packet(packet: Packet) -> Union[str, bytes, 'Image.Image']:
        """
        Extract raw data from Packet.

        Returns the underlying content from a Packet object,
        stripping away the metadata wrapper.

        Args:
            packet: Packet to extract data from

        Returns:
            Raw content (str, bytes, or PIL.Image.Image)

        Examples:
            >>> packet = Packet.from_text("Hello")
            >>> data = PacketConverter.from_packet(packet)
            >>> data
            'Hello'

            >>> packet = Packet.from_bytes(b"binary")
            >>> data = PacketConverter.from_packet(packet)
            >>> data
            b'binary'
        """
        return packet.content
