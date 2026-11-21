
import csv
import json
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from docx import Document
from pypdf import PdfReader

class DataLoader:
    SUPPORTED_EXTENSIONS = {
        ".txt",
        ".md",
        ".pdf",
        ".docx",
        ".csv",
        ".json",
    }

    def __init__(
        self,
        folder: str | Path,
        chunk_size: int = 800,
        overlap: int = 100,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be between 0 and chunk_size - 1")

        self.folder = Path(folder)
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", " ", ""],
            length_function=len,
        )

    def load(self) -> list[dict]:
        if not self.folder.is_dir():
            raise NotADirectoryError(self.folder)

        chunks = []

        for path in sorted(self.folder.rglob("*")):
            if not path.is_file():
                continue

            if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue

            chunks.extend(self.load_file(path))

        return chunks

    def load_file(self, path: Path) -> list[dict]:
        extension = path.suffix.lower()
        source = path.relative_to(self.folder).as_posix()

        try:
            if extension == ".json":
                return self.load_json(path, source)

            text = self.read_text(path, extension)

        except (OSError, ValueError, KeyError) as error:
            print(f"Skipped {path.name}: {error}")
            return []

        if not text or not text.strip():
            print(f"Skipped {path.name}: empty document")
            return []

        return [
            {
                "id": f"{source}::{number}",
                "title": path.stem,
                "section": path.parent.name,
                "text": piece,
                "source": source,
                "source_type": extension.lstrip("."),
            }
            for number, piece in enumerate(self.split(text))
        ]

    def load_json(self, path: Path, source: str) -> list[dict]:
        data = json.loads(path.read_text(encoding="utf-8"))

        if not isinstance(data, list):
            raise ValueError("JSON must contain a list of objects")

        chunks = []

        for number, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(f"JSON item {number} must be an object")

            if not isinstance(item.get("text"), str):
                raise ValueError(f"JSON item {number} must contain text")

            chunk = item.copy()
            chunk.setdefault("id", f"{source}::{number}")
            chunk.setdefault("source", source)
            chunk.setdefault("source_type", "json")

            chunks.append(chunk)

        return chunks

    def read_text(self, path: Path, extension: str) -> str:
        if extension in (".txt", ".md"):
            return path.read_text(encoding="utf-8")

        if extension == ".pdf":
            reader = PdfReader(path)
            return "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        if extension == ".docx":
            document = Document(path)

            paragraphs = [
                paragraph.text
                for paragraph in document.paragraphs
                if paragraph.text.strip()
            ]

            tables = [
                "\n".join(
                    " | ".join(cell.text for cell in row.cells)
                    for row in table.rows
                )
                for table in document.tables
            ]

            return "\n\n".join(paragraphs + tables)

        if extension == ".csv":
            with path.open(
                encoding="utf-8-sig",
                newline=""
            ) as csv_file:
                return "\n".join(
                    ", ".join(row)
                    for row in csv.reader(csv_file)
                )

        raise ValueError(f"Unsupported file extension: {extension}")

    def split(self, text):
        return self.text_splitter.split_text(text)
