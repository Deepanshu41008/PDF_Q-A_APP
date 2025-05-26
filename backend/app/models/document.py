from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class Document(Base):
    """
    Represents a single uploaded document in the system.

    Columns
    -------
    id : int
        Auto-increment primary key.
    title : str | None
        Human-readable title for the document.
    filename : str
        Name of the file stored in the system.
    file_path : str
        Absolute (or repo-relative) path where the document is stored.
    index_path : str | None
        Directory where the vector index is saved.
    upload_date : datetime
        UTC timestamp when the row was created.
    file_size : int | None
        Size of the file in bytes.
    page_count : int | None
        Number of pages in the document.
    """

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    index_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    upload_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<Document id={self.id}, title={self.title!r}, filename={self.filename!r}>"

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable representation of the row."""
        return {
            "id": self.id,
            "title": self.title,
            "filename": self.filename,
            "file_path": self.file_path,
            "index_path": self.index_path,
            "upload_date": self.upload_date.isoformat() if self.upload_date is not None else None,
            "file_size": self.file_size,
            "page_count": self.page_count,
        }
