from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Evidence(StrictModel):
    passage_id: str = Field(min_length=1, max_length=100)
    quote: str = Field(min_length=1, max_length=600)


class GeneratedSection(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,60}$")
    kind: Literal["objectives", "introduction", "readings", "notes", "announcement", "assignment", "rubric", "quiz"]
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=12000)
    answer: str | None
    explanation: str | None
    evidence: list[Evidence] = Field(max_length=12)


class GeneratedCourse(StrictModel):
    sections: list[GeneratedSection] = Field(min_length=1, max_length=20)


class SupportResult(StrictModel):
    section_id: str
    status: Literal["supported", "unsupported", "conflicting", "insufficient"]
    reason: str = Field(max_length=1000)


class Verification(StrictModel):
    results: list[SupportResult]


class CourseInput(StrictModel):
    document_id: str
    title: str = Field(min_length=1, max_length=150)
    difficulty: Literal["introductory", "intermediate", "advanced"] = "introductory"
    modules: Literal[1] = 1
    assignments: Literal[1] = 1
    quizzes: Literal[1] = 1
    questions_per_quiz: int = Field(default=3, ge=1, le=5)
    mode: Literal["demo", "openai"] = "openai"


class OutlineEdit(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    module_title: str | None = Field(default=None, min_length=1, max_length=150)
    objectives: list[str] | None = Field(default=None, min_length=1, max_length=8)


class Approval(StrictModel):
    provider_disclosure_accepted: Literal[True]


class GenerateInput(StrictModel):
    idempotency_key: str = Field(min_length=8, max_length=100)
    section_id: str | None = None


class SectionEdit(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = Field(default=None, min_length=1, max_length=12000)
    answer: str | None = Field(default=None, max_length=4000)
    explanation: str | None = Field(default=None, max_length=4000)


class ReorderInput(StrictModel):
    section_ids: list[str]
