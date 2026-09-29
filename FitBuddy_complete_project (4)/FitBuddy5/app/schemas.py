from typing import Literal

from pydantic import BaseModel, Field, field_validator


Goal = str
Intensity = Literal["low", "medium", "high"]


class UserInput(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    user_id: str = Field(min_length=1, max_length=50)
    age: int = Field(ge=13, le=120)
    weight: float = Field(gt=20, le=500)
    goal: str = Field(min_length=2, max_length=100)
    intensity: Intensity

    @field_validator("username", "user_id", "goal")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty.")
        return value


class FeedbackRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=50)
    feedback: str = Field(min_length=3, max_length=2000)

    @field_validator("user_id", "feedback")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty.")
        return value
