from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .lab import Lab
    from .status import ImplementationStatus


class AlgorithmBase(SQLModel):
    name: str = Field(index=True)
    slug: str = Field(unique=True, index=True)
    category: str = Field(index=True)        # URL slug (e.g., "supervised")
    subcategory: str = Field(index=True)     # e.g., "classification"
    year: Optional[int] = None
    author: Optional[str] = None
    paper_reference: Optional[str] = None
    complexity: str = Field(default="medium")  # "low" | "medium" | "high"
    best_use_case: Optional[str] = None
    description: Optional[str] = None
    compatibility_tabular: bool = False
    compatibility_image: bool = False
    compatibility_text: bool = False
    compatibility_graph: bool = False
    compatibility_timeseries: bool = False


class Algorithm(AlgorithmBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    parameters: List["AlgorithmParameter"] = Relationship(back_populates="algorithm")
    notes: List["AlgorithmNote"] = Relationship(back_populates="algorithm")
    lab: Optional["Lab"] = Relationship(back_populates="algorithm")
    status: Optional["ImplementationStatus"] = Relationship(back_populates="algorithm")


class AlgorithmParameter(SQLModel, table=True):
    __tablename__ = "algorithm_parameters"

    id: Optional[int] = Field(default=None, primary_key=True)
    algorithm_id: int = Field(foreign_key="algorithm.id", index=True)
    parameter_name: str
    description: Optional[str] = None
    default_value: Optional[str] = None
    parameter_type: str = Field(default="float")  # "float" | "int" | "str" | "bool"
    algorithm: Optional[Algorithm] = Relationship(back_populates="parameters")


class AlgorithmNote(SQLModel, table=True):
    __tablename__ = "algorithm_notes"

    id: Optional[int] = Field(default=None, primary_key=True)
    algorithm_id: int = Field(foreign_key="algorithm.id", index=True)
    note_type: str = Field(default="research")  # "research" | "implementation" | "insight" | "question"
    content: str
    created_at: Optional[str] = None  # ISO datetime string
    algorithm: Optional[Algorithm] = Relationship(back_populates="notes")
