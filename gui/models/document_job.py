from dataclasses import dataclass
from enum import Enum
from typing import Optional

class DocumentSourceType(Enum):
    PDF = "pdf"
    TXT = "txt"
    CLIPBOARD = "clipboard"

@dataclass
class DocumentJob:
    id: str
    source_type: DocumentSourceType
    filepath: Optional[str]  # Puede ser nulo si es clipboard
    content: Optional[str]   # Contenido si es clipboard o txt cargado en memoria
    status: str
    progress: int
