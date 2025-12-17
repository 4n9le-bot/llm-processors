"""
FilterProcessor: Filter packets by substream_name metadata.

This processor allows selective processing of packets based on their
substream_name metadata, enabling fine-grained control over packet routing
in complex pipelines.
"""

from typing import AsyncIterable, AsyncIterator, Optional, Union

from llm_processors.core import Packet, BaseProcessor


class FilterProcessor(BaseProcessor):
    """
    Filter packets by substream_name metadata.

    Allows inclusion (whitelist) or exclusion (blacklist) of packets
    based on their substream_name metadata. This is useful for routing
    packets in complex pipelines, especially after parallel processing.

    Examples:
        >>> # Include only specific substreams
        >>> filter_proc = FilterProcessor(include="branch_0")
        >>> pipeline = parallel_proc + filter_proc + next_proc

        >>> # Exclude error packets
        >>> no_errors = FilterProcessor(exclude="error")
        >>> pipeline = processor + no_errors + next_processor

        >>> # Multiple includes
        >>> filter_proc = FilterProcessor(include=["branch_0", "branch_1"])
    """

    def __init__(
        self,
        include: Optional[Union[str, list[str]]] = None,
        exclude: Optional[Union[str, list[str]]] = None
    ):
        """
        Initialize filter processor.

        Args:
            include: Substream name(s) to include (whitelist).
                If specified, only packets with matching substream_name pass through.
                Can be a single string or list of strings.
            exclude: Substream name(s) to exclude (blacklist).
                If specified, packets with matching substream_name are filtered out.
                Can be a single string or list of strings.

        Note:
            - If both include and exclude are None, all packets pass through
            - If both are specified, include takes precedence (packet must be in
              include list AND not in exclude list)
            - Packets without substream_name metadata are treated as having
              substream_name=None

        Examples:
            >>> # Include only branch_0
            >>> FilterProcessor(include="branch_0")

            >>> # Exclude errors
            >>> FilterProcessor(exclude="error")

            >>> # Include multiple branches
            >>> FilterProcessor(include=["branch_0", "branch_1"])

            >>> # Include specific branches but exclude errors
            >>> FilterProcessor(include=["branch_0", "branch_1"], exclude="error")
        """
        super().__init__()

        # Normalize include to set
        if include is None:
            self.include: Optional[set[str]] = None
        elif isinstance(include, str):
            self.include = {include}
        else:
            self.include = set(include)

        # Normalize exclude to set
        if exclude is None:
            self.exclude: Optional[set[str]] = None
        elif isinstance(exclude, str):
            self.exclude = {exclude}
        else:
            self.exclude = set(exclude)

    def _should_pass(self, packet: Packet) -> bool:
        """
        Check if packet should pass through the filter.

        Args:
            packet: Packet to check

        Returns:
            True if packet should pass, False otherwise
        """
        substream = packet.substream_name

        # Check include filter
        if self.include is not None:
            if substream not in self.include:
                return False

        # Check exclude filter
        if self.exclude is not None:
            if substream in self.exclude:
                return False

        return True

    async def _process_stream(
        self,
        stream: AsyncIterable[Packet]
    ) -> AsyncIterator[Packet]:
        """
        Filter packets based on substream_name.

        Args:
            stream: Input packet stream

        Yields:
            Packets that pass the filter criteria
        """
        async for packet in stream:
            if self._should_pass(packet):
                yield packet

    def __repr__(self) -> str:
        """String representation."""
        parts = []
        if self.include is not None:
            parts.append(f"include={sorted(self.include)}")
        if self.exclude is not None:
            parts.append(f"exclude={sorted(self.exclude)}")

        if not parts:
            return "FilterProcessor(pass_all)"

        return f"FilterProcessor({', '.join(parts)})"
