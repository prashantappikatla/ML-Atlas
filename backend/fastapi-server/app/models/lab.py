from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .algorithm import Algorithm


class Lab(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    algorithm_id: int = Field(foreign_key="algorithm.id", unique=True, index=True)
    lab_name: str
    lab_type: str = Field(default="visualization")
    # "visualization" | "parameter-tuning" | "training-demo" | "dataset-experiment"
    url: Optional[str] = None
    framework: str = Field(default="streamlit")  # "streamlit" | "gradio"
    algorithm: Optional["Algorithm"] = Relationship(back_populates="lab")
