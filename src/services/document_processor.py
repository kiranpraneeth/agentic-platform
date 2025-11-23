"""Document processing service for RAG."""

import hashlib
import re
from io import BytesIO
from typing import Any

import aiofiles
import tiktoken
from bs4 import BeautifulSoup
from docx import Document as DocxDocument
from markdown import markdown
from pypdf import PdfReader


class DocumentProcessor:
    """Process documents into chunks for RAG."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """Initialize document processor.

        Args:
            chunk_size: Target size for each chunk in tokens
            chunk_overlap: Number of overlapping tokens between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # OpenAI's encoding

    async def process_file(
        self, file_content: bytes, content_type: str, filename: str
    ) -> tuple[str, list[dict[str, Any]]]:
        """Process a file and return extracted text and chunks.

        Args:
            file_content: File bytes
            content_type: MIME type or file extension
            filename: Original filename

        Returns:
            Tuple of (full_text, list of chunk dictionaries)
        """
        # Extract text based on content type
        if content_type in ["pdf", "application/pdf"]:
            text = await self._extract_pdf(file_content)
        elif content_type in ["docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            text = await self._extract_docx(file_content)
        elif content_type in ["txt", "text/plain"]:
            text = file_content.decode("utf-8", errors="ignore")
        elif content_type in ["md", "markdown", "text/markdown"]:
            text = await self._extract_markdown(file_content)
        elif content_type in ["html", "text/html"]:
            text = await self._extract_html(file_content)
        else:
            # Fallback: try to decode as text
            text = file_content.decode("utf-8", errors="ignore")

        # Clean text
        text = self._clean_text(text)

        # Create chunks
        chunks = self._create_chunks(text)

        return text, chunks

    async def _extract_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF."""
        text_parts = []
        pdf = PdfReader(BytesIO(file_content))

        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"\n--- Page {page_num} ---\n{page_text}")

        return "\n".join(text_parts)

    async def _extract_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX."""
        doc = DocxDocument(BytesIO(file_content))
        text_parts = []

        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)

        return "\n\n".join(text_parts)

    async def _extract_markdown(self, file_content: bytes) -> str:
        """Extract text from Markdown by converting to HTML then extracting text."""
        md_text = file_content.decode("utf-8", errors="ignore")
        html = markdown(md_text)
        return await self._extract_html(html.encode("utf-8"))

    async def _extract_html(self, file_content: bytes) -> str:
        """Extract text from HTML."""
        html = file_content.decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text
        text = soup.get_text()
        return text

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove excessive newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def _create_chunks(self, text: str) -> list[dict[str, Any]]:
        """Create overlapping chunks from text.

        Args:
            text: Full text to chunk

        Returns:
            List of chunk dictionaries with content, tokens, and metadata
        """
        # Tokenize the full text
        tokens = self.tokenizer.encode(text)
        total_tokens = len(tokens)

        chunks = []
        start = 0
        sequence = 0

        while start < total_tokens:
            # Get chunk tokens
            end = min(start + self.chunk_size, total_tokens)
            chunk_tokens = tokens[start:end]

            # Decode back to text
            chunk_text = self.tokenizer.decode(chunk_tokens)

            # Try to find sentence boundaries for cleaner chunks
            if end < total_tokens:  # Not the last chunk
                # Look for sentence endings in the last 20% of the chunk
                search_start = int(len(chunk_text) * 0.8)
                sentence_match = re.search(
                    r"[.!?]\s+", chunk_text[search_start:]
                )
                if sentence_match:
                    # Split at sentence boundary
                    split_pos = search_start + sentence_match.end()
                    chunk_text = chunk_text[:split_pos].strip()
                    # Recalculate actual tokens used
                    chunk_tokens = self.tokenizer.encode(chunk_text)

            chunks.append({
                "content": chunk_text.strip(),
                "sequence_number": sequence,
                "token_count": len(chunk_tokens),
                "start_char": start,
                "end_char": start + len(chunk_text),
            })

            # Move to next chunk with overlap
            start += self.chunk_size - self.chunk_overlap
            sequence += 1

        return chunks

    @staticmethod
    def calculate_file_hash(file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content.

        Args:
            file_content: File bytes

        Returns:
            Hex string of SHA-256 hash
        """
        return hashlib.sha256(file_content).hexdigest()

    @staticmethod
    def get_content_type(filename: str) -> str:
        """Determine content type from filename.

        Args:
            filename: Filename with extension

        Returns:
            Content type string
        """
        ext = filename.lower().split(".")[-1] if "." in filename else "txt"

        content_type_map = {
            "pdf": "pdf",
            "docx": "docx",
            "doc": "docx",
            "txt": "txt",
            "md": "md",
            "markdown": "md",
            "html": "html",
            "htm": "html",
            "json": "json",
            "csv": "csv",
        }

        return content_type_map.get(ext, "txt")


class ChunkingStrategy:
    """Different chunking strategies for documents."""

    @staticmethod
    def fixed_size_chunking(
        text: str, chunk_size: int, overlap: int, tokenizer: Any
    ) -> list[dict[str, Any]]:
        """Fixed-size chunking with overlap (default strategy)."""
        processor = DocumentProcessor(chunk_size=chunk_size, chunk_overlap=overlap)
        return processor._create_chunks(text)

    @staticmethod
    def semantic_chunking(text: str, max_chunk_size: int = 512) -> list[dict[str, Any]]:
        """Chunk by paragraphs and sections, respecting semantic boundaries."""
        chunks = []
        paragraphs = text.split("\n\n")
        tokenizer = tiktoken.get_encoding("cl100k_base")

        current_chunk = []
        current_tokens = 0
        sequence = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_tokens = len(tokenizer.encode(para))

            if current_tokens + para_tokens <= max_chunk_size:
                current_chunk.append(para)
                current_tokens += para_tokens
            else:
                # Save current chunk if not empty
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append({
                        "content": chunk_text,
                        "sequence_number": sequence,
                        "token_count": current_tokens,
                        "start_char": 0,  # Would need to track positions
                        "end_char": len(chunk_text),
                    })
                    sequence += 1

                # Start new chunk
                current_chunk = [para]
                current_tokens = para_tokens

        # Add last chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append({
                "content": chunk_text,
                "sequence_number": sequence,
                "token_count": current_tokens,
                "start_char": 0,
                "end_char": len(chunk_text),
            })

        return chunks

    @staticmethod
    def sentence_based_chunking(text: str, sentences_per_chunk: int = 5) -> list[dict[str, Any]]:
        """Chunk by sentences."""
        # Simple sentence splitting
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks = []
        tokenizer = tiktoken.get_encoding("cl100k_base")

        for i in range(0, len(sentences), sentences_per_chunk):
            chunk_sentences = sentences[i:i + sentences_per_chunk]
            chunk_text = " ".join(chunk_sentences)
            chunks.append({
                "content": chunk_text,
                "sequence_number": i // sentences_per_chunk,
                "token_count": len(tokenizer.encode(chunk_text)),
                "start_char": 0,
                "end_char": len(chunk_text),
            })

        return chunks
