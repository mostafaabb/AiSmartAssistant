"""
Code execution routes for NexusAI API.
Handles code execution in various languages.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import subprocess
import logging
from typing import Optional

from backend.app.core import get_db, get_current_user, settings
from backend.app.models import CodeExecution, Project
from backend.app.schemas import (
    CodeExecutionRequest,
    CodeExecutionResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/projects", tags=["Code Execution"])


# Language-specific execution commands
LANGUAGE_EXECUTORS = {
    "python": ["python", "-c"],
    "python3": ["python3", "-c"],
    "javascript": ["node", "-e"],
    "js": ["node", "-e"],
    "bash": ["bash", "-c"],
    "sh": ["sh", "-c"],
    "ruby": ["ruby", "-e"],
    "php": ["php", "-r"],
    "go": ["go", "run"],  # Special handling
    "rust": ["rustc", "--run"],  # Special handling
}


async def execute_code(code: str, language: str, stdin: Optional[str] = None, timeout: int = None) -> dict:
    """
    Execute code in a subprocess.

    Args:
        code: Source code to execute
        language: Programming language
        stdin: Standard input for the program
        timeout: Execution timeout in seconds

    Returns:
        Dictionary with output, error, status, and execution_time
    """
    if timeout is None:
        timeout = settings.code_execution_timeout

    executor = LANGUAGE_EXECUTORS.get(language.lower())

    if not executor:
        return {
            "status": "error",
            "error": f"Language '{language}' not supported",
            "output": None,
            "execution_time": 0,
        }

    try:
        # Build command
        if language.lower() == "go":
            # Go requires special handling (needs file)
            return {
                "status": "error",
                "error": "Go requires file-based execution. Use file API instead.",
                "output": None,
            }

        cmd = executor + [code]

        # Execute with timeout
        result = subprocess.run(
            cmd,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout,
            "error": result.stderr,
            "execution_time": 0,
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "error": f"Execution timeout ({timeout}s exceeded)",
            "output": None,
            "execution_time": timeout * 1000,
        }
    except Exception as e:
        logger.error(f"Execution error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "output": None,
        }


@router.post("/{project_id}/code/execute", response_model=CodeExecutionResponse)
async def run_code(
    project_id: UUID,
    request: CodeExecutionRequest,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute code in a project context.

    Args:
        project_id: Project ID
        request: Code execution request (code, language, optional stdin)
        current_user_id: Current user ID
        db: Database session

    Returns:
        CodeExecutionResponse with output and status

    Raises:
        HTTPException 404: Project not found
        HTTPException 400: Invalid language or code
    """
    # Verify project exists
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Validate code
    if not request.code or len(request.code) > 100000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid code (empty or too large)"
        )

    # Create execution record
    execution = CodeExecution(
        project_id=project_id,
        code=request.code,
        language=request.language,
        status="running",
    )

    db.add(execution)
    await db.commit()

    try:
        # Execute code
        result = await execute_code(
            request.code,
            request.language,
            request.stdin,
            settings.code_execution_timeout,
        )

        # Update execution record
        execution.status = result["status"]
        execution.output = result.get("output")
        execution.error = result.get("error")
        execution.execution_time = result.get("execution_time")

        await db.commit()
        await db.refresh(execution)

        logger.info(f"✅ Code executed: {project_id} ({request.language})")

        return CodeExecutionResponse.from_orm(execution)

    except Exception as e:
        execution.status = "error"
        execution.error = str(e)
        await db.commit()

        logger.error(f"Execution error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Code execution failed"
        )


@router.get("/{project_id}/code/executions")
async def list_executions(
    project_id: UUID,
    limit: int = 50,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get execution history for a project."""
    result = await db.execute(
        select(CodeExecution)
        .where(CodeExecution.project_id == project_id)
        .order_by(CodeExecution.created_at.desc())
        .limit(limit)
    )
    executions = result.scalars().all()

    return [CodeExecutionResponse.from_orm(e) for e in executions]


@router.get("/{project_id}/code/executions/{execution_id}", response_model=CodeExecutionResponse)
async def get_execution(
    project_id: UUID,
    execution_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific code execution."""
    result = await db.execute(
        select(CodeExecution).where(
            (CodeExecution.id == execution_id) &
            (CodeExecution.project_id == project_id)
        )
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )

    return CodeExecutionResponse.from_orm(execution)
