"""
Pydantic schemas for request/response validation in NexusAI.
These define the shape of data coming in and going out of the API.
"""

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ======================== AUTH SCHEMAS ========================

class UserRegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v):
        assert v.isalnum() or "_" in v, "Username must be alphanumeric"
        return v


class UserLoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """User data response (safe to share)."""
    id: UUID
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# ======================== ORGANIZATION SCHEMAS ========================

class OrganizationCreateRequest(BaseModel):
    """Create organization request."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class OrganizationUpdateRequest(BaseModel):
    """Update organization request."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class OrganizationResponse(BaseModel):
    """Organization response."""
    id: UUID
    name: str
    description: Optional[str]
    owner_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ======================== PROJECT SCHEMAS ========================

class ProjectCreateRequest(BaseModel):
    """Create project request."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    git_url: Optional[str] = None


class ProjectUpdateRequest(BaseModel):
    """Update project request."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class ProjectResponse(BaseModel):
    """Project response."""
    id: UUID
    organization_id: UUID
    name: str
    description: Optional[str]
    git_url: Optional[str]
    git_branch: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ======================== FILE SCHEMAS ========================

class FileCreateRequest(BaseModel):
    """Create file request."""
    path: str = Field(..., min_length=1, max_length=500)
    content: str = ""
    language: str = Field(..., max_length=50)


class FileUpdateRequest(BaseModel):
    """Update file request."""
    content: str
    commit_message: Optional[str] = None


class FileResponse(BaseModel):
    """File response."""
    id: UUID
    project_id: UUID
    path: str
    content: str
    language: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FileVersionResponse(BaseModel):
    """File version response."""
    id: UUID
    content: str
    created_at: datetime
    commit_message: Optional[str]

    class Config:
        from_attributes = True


# ======================== CODE EXECUTION SCHEMAS ========================

class CodeExecutionRequest(BaseModel):
    """Code execution request."""
    code: str
    language: str = Field(..., max_length=50)
    stdin: Optional[str] = None


class CodeExecutionResponse(BaseModel):
    """Code execution response."""
    id: UUID
    language: str
    status: str  # pending, running, success, error, timeout
    output: Optional[str]
    error: Optional[str]
    execution_time: Optional[int]  # milliseconds
    created_at: datetime

    class Config:
        from_attributes = True


# ======================== CHAT SCHEMAS ========================

class ChatMessage(BaseModel):
    """Single chat message."""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Chat request."""
    messages: List[ChatMessage]
    model: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response."""
    role: str = "assistant"
    content: str


# ======================== SESSION SCHEMAS ========================

class SessionResponse(BaseModel):
    """Session response."""
    id: UUID
    user_id: UUID
    project_id: Optional[UUID]
    code_context: Dict[str, Any]
    chat_history: List[ChatMessage]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionUpdateRequest(BaseModel):
    """Update session request."""
    code_context: Optional[Dict[str, Any]] = None
    chat_history: Optional[List[ChatMessage]] = None
    last_execution_error: Optional[str] = None


# ======================== ERROR SCHEMAS ========================

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    error: str = "validation_error"
    details: List[Dict[str, Any]]


# ======================== HEALTH CHECK SCHEMAS ========================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str
    timestamp: datetime
    database: str = "connected"
