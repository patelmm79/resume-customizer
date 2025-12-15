"""Pydantic schemas for agent responses to enable structured output."""
from pydantic import BaseModel, Field
from typing import List


class SuggestionSchema(BaseModel):
    """Schema for a single suggestion from Agent 1."""
    category: str = Field(description="Category of the suggestion (Skills, Experience, Summary, etc.)")
    text: str = Field(description="Brief description of the suggestion shown in checkbox")
    suggested_text: str = Field(description="The complete text to insert/replace")


class ResumeAnalysisSchema(BaseModel):
    """Schema for Agent 1 resume analysis response."""
    score: int = Field(description="Compatibility score from 1-100", ge=1, le=100)
    analysis: str = Field(description="Detailed analysis explaining the score")
    suggestions: List[SuggestionSchema] = Field(description="List of actionable suggestions")


class ResumeScoreSchema(BaseModel):
    """Schema for Agent 1 score-only response (rescoring)."""
    score: int = Field(description="Compatibility score from 1-100", ge=1, le=100)
    analysis: str = Field(description="Brief analysis of the match quality")


class OptimizationSuggestionSchema(BaseModel):
    """Schema for a single optimization suggestion from Agent 5."""
    category: str = Field(description="Category of optimization (Brevity, Clarity, Impact, etc.)")
    description: str = Field(description="Description of what will be optimized")
    impact: str = Field(description="Expected impact (e.g., 'Removes 50 words')")


class OptimizationAnalysisSchema(BaseModel):
    """Schema for Agent 5 optimization analysis (suggestion phase)."""
    analysis: str = Field(description="Analysis of optimization opportunities")
    current_word_count: int = Field(description="Current word count before optimization")
    suggestions: List[OptimizationSuggestionSchema] = Field(description="List of optimization suggestions")


class OptimizedResumeSchema(BaseModel):
    """Schema for Agent 5 optimized resume (application phase)."""
    optimized_resume: str = Field(description="The optimized resume content")
    word_count_before: int = Field(description="Word count before optimization")
    word_count_after: int = Field(description="Word count after optimization")
    words_removed: int = Field(description="Number of words removed")
    summary: str = Field(description="Summary of optimizations applied")
    changes_made: List[str] = Field(description="List of specific changes made")


# Agent 3 Schemas
class RescoreSchema(BaseModel):
    """Schema for Agent 3 rescoring response."""
    new_score: int = Field(description="New compatibility score from 1-100", ge=1, le=100)
    comparison: str = Field(description="Brief comparison of how the resume has changed")
    improvements: List[str] = Field(description="Key improvements made to the resume")
    concerns: List[str] = Field(description="Remaining concerns or areas for improvement")
    recommendation: str = Field(description="Either 'Ready to Submit' or 'Needs More Work'")
    reasoning: str = Field(description="Explanation of why ready or needs work")
    score_drop_explanation: str = Field(default="", description="ONLY IF NEW SCORE < ORIGINAL: Detailed explanation of why score dropped")


# Agent 4 Schemas
class ValidationIssueSchema(BaseModel):
    """Schema for a single validation issue from Agent 4."""
    severity: str = Field(description="CRITICAL, WARNING, or INFO")
    category: str = Field(description="Category like Markdown, Date Format, Bullet Style, etc.")
    description: str = Field(description="Description of the formatting issue")


class ValidationSchema(BaseModel):
    """Schema for Agent 4 validation response."""
    validation_score: int = Field(description="Formatting quality score from 1-100", ge=1, le=100)
    is_valid: bool = Field(description="True if passes validation (score >= 80 and no critical issues)")
    issues: List[ValidationIssueSchema] = Field(description="List of formatting issues found")
    recommendations: List[str] = Field(description="Formatting recommendations")
    summary: str = Field(description="Brief summary of formatting quality")
