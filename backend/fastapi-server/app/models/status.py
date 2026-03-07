from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .algorithm import Algorithm


class ImplementationStatus(SQLModel, table=True):
    __tablename__ = "implementation_status"

    id: Optional[int] = Field(default=None, primary_key=True)
    algorithm_id: int = Field(foreign_key="algorithm.id", unique=True, index=True)
    status: str = Field(default="planned")
    # "planned" | "in-progress" | "documented" | "implemented" | "lab-ready"
    implemented_from_scratch: bool = False
    implemented_library: bool = False
    lab_created: bool = False
    documentation_complete: bool = False
    notes_added: bool = False
    last_updated: Optional[str] = None  # ISO datetime string
    algorithm: Optional["Algorithm"] = Relationship(back_populates="status")
