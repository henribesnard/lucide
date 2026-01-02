"""
Message Formatter Utility

Handles formatting messages for Telegram's Markdown/HTML support.
"""
import re
from typing import List


class MessageFormatter:
    """Utility class for formatting messages for Telegram."""

    @staticmethod
    def format_for_telegram(text: str, max_length: int = 4096) -> str:
        """
        Format text for Telegram Markdown.

        Telegram uses MarkdownV2 which requires escaping special characters.
        However, we'll use standard Markdown with some sanitization.

        Args:
            text: Raw text to format
            max_length: Maximum message length (Telegram limit is 4096)

        Returns:
            Formatted text suitable for Telegram
        """
        if not text:
            return ""

        # Truncate if too long
        if max_length and max_length > 0 and len(text) > max_length:
            text = text[: max_length - 3] + "..."

        return text

    @staticmethod
    def escape_markdown_v2(text: str) -> str:
        """
        Escape special characters for MarkdownV2.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        special_chars = [
            "_",
            "*",
            "[",
            "]",
            "(",
            ")",
            "~",
            "`",
            ">",
            "#",
            "+",
            "-",
            "=",
            "|",
            "{",
            "}",
            ".",
            "!",
        ]

        for char in special_chars:
            text = text.replace(char, f"\\{char}")

        return text

    @staticmethod
    def split_long_message(text: str, max_length: int = 4000) -> List[str]:
        """
        Split a long message into multiple parts.

        Splits on paragraph boundaries when possible.

        Args:
            text: Text to split
            max_length: Maximum length per part (leave buffer for formatting)

        Returns:
            List of message parts
        """
        if len(text) <= max_length:
            return [text]

        parts = []
        current_part = ""

        # Split by paragraphs
        paragraphs = text.split("\n\n")

        for paragraph in paragraphs:
            # If adding this paragraph would exceed limit
            if len(current_part) + len(paragraph) + 2 > max_length:
                # If current_part is not empty, save it
                if current_part:
                    parts.append(current_part.strip())
                    current_part = ""

                # If single paragraph is too long, split by sentences
                if len(paragraph) > max_length:
                    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
                    for sentence in sentences:
                        if len(current_part) + len(sentence) + 1 > max_length:
                            if current_part:
                                parts.append(current_part.strip())
                            current_part = sentence
                        else:
                            current_part += " " + sentence if current_part else sentence
                else:
                    current_part = paragraph
            else:
                current_part += "\n\n" + paragraph if current_part else paragraph

        # Add remaining part
        if current_part:
            parts.append(current_part.strip())

        return parts

    @staticmethod
    def format_match_analysis(analysis: dict) -> str:
        """
        Format match analysis for Telegram.

        Args:
            analysis: Analysis dictionary from Lucide pipeline

        Returns:
            Formatted message
        """
        # This is a placeholder for match analysis formatting
        # The actual formatting will depend on the analysis structure
        return str(analysis)

    @staticmethod
    def format_table(rows: List[List[str]], headers: List[str] = None) -> str:
        """
        Format a table using monospace text.

        Args:
            rows: List of rows, each row is a list of cell values
            headers: Optional header row

        Returns:
            Formatted table as monospace text block
        """
        if not rows:
            return ""

        # Calculate column widths
        all_rows = [headers] + rows if headers else rows
        col_widths = [
            max(len(str(row[i])) for row in all_rows) for i in range(len(all_rows[0]))
        ]

        # Format rows
        formatted_rows = []

        if headers:
            header_row = " | ".join(
                str(headers[i]).ljust(col_widths[i]) for i in range(len(headers))
            )
            formatted_rows.append(header_row)
            formatted_rows.append("-" * len(header_row))

        for row in rows:
            formatted_row = " | ".join(
                str(row[i]).ljust(col_widths[i]) for i in range(len(row))
            )
            formatted_rows.append(formatted_row)

        return "```\n" + "\n".join(formatted_rows) + "\n```"
