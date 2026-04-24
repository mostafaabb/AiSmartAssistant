"""
Git integration service for NexusAI.
Handles repository cloning, commits, pushes, and branch management.
"""

import subprocess
import tempfile
import logging
from typing import Optional, List, Dict
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class GitService:
    """
    Git operations for projects.
    Handles cloning, committing, pushing, and branch management.
    """

    def __init__(self, workspace_dir: str = "./workspace"):
        self.workspace_dir = workspace_dir

    def _get_project_dir(self, project_id: str) -> str:
        """Get project directory path."""
        return os.path.join(self.workspace_dir, str(project_id))

    async def clone_repository(
        self,
        project_id: str,
        git_url: str,
        branch: str = "main",
    ) -> Dict[str, str]:
        """
        Clone a Git repository.

        Args:
            project_id: Project ID
            git_url: GitHub/GitLab URL
            branch: Branch to clone

        Returns:
            Result with status and message
        """
        try:
            project_dir = self._get_project_dir(project_id)

            # Create directory if not exists
            Path(project_dir).mkdir(parents=True, exist_ok=True)

            # Clone repository
            cmd = [
                "git", "clone",
                "--branch", branch,
                git_url,
                project_dir
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                logger.info(f"✅ Cloned repo: {git_url} → {project_dir}")
                return {
                    "status": "success",
                    "message": f"Repository cloned successfully",
                    "branch": branch,
                }
            else:
                logger.error(f"Clone failed: {result.stderr}")
                return {
                    "status": "error",
                    "message": f"Clone failed: {result.stderr}",
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "Clone operation timed out",
            }
        except Exception as e:
            logger.error(f"Clone error: {e}")
            return {
                "status": "error",
                "message": str(e),
            }

    async def commit(
        self,
        project_id: str,
        message: str,
        author_name: str = "NexusAI",
        author_email: str = "ai@nexusai.dev",
    ) -> Dict[str, str]:
        """
        Commit staged changes.

        Args:
            project_id: Project ID
            message: Commit message
            author_name: Author name
            author_email: Author email

        Returns:
            Result with commit hash
        """
        try:
            project_dir = self._get_project_dir(project_id)

            # Set git user for this repo
            subprocess.run(
                ["git", "config", "user.name", author_name],
                cwd=project_dir,
                capture_output=True,
                timeout=10,
            )
            subprocess.run(
                ["git", "config", "user.email", author_email],
                cwd=project_dir,
                capture_output=True,
                timeout=10,
            )

            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                logger.info(f"✅ Commit created: {message[:50]}")
                return {
                    "status": "success",
                    "message": "Changes committed",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Commit failed: {result.stderr}",
                }

        except Exception as e:
            logger.error(f"Commit error: {e}")
            return {
                "status": "error",
                "message": str(e),
            }

    async def push(
        self,
        project_id: str,
        branch: str = "main",
        token: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Push commits to remote.

        Args:
            project_id: Project ID
            branch: Branch to push
            token: GitHub/GitLab token for authentication

        Returns:
            Result with status
        """
        try:
            project_dir = self._get_project_dir(project_id)

            # Get remote URL
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )
            remote_url = result.stdout.strip()

            # Update remote with token if provided
            if token:
                # Parse URL and inject token
                if remote_url.startswith("https://"):
                    remote_url = remote_url.replace(
                        "https://",
                        f"https://oauth:{token}@"
                    )

            # Push
            push_result = subprocess.run(
                ["git", "push", "origin", branch],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=60,
                env={**os.environ, "GIT_ASKPASS": "/bin/echo"},
            )

            if push_result.returncode == 0:
                logger.info(f"✅ Pushed to {remote_url}")
                return {
                    "status": "success",
                    "message": "Changes pushed to remote",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Push failed: {push_result.stderr}",
                }

        except Exception as e:
            logger.error(f"Push error: {e}")
            return {
                "status": "error",
                "message": str(e),
            }

    async def pull(
        self,
        project_id: str,
        branch: str = "main",
    ) -> Dict[str, str]:
        """
        Pull changes from remote.

        Args:
            project_id: Project ID
            branch: Branch to pull

        Returns:
            Result with status
        """
        try:
            project_dir = self._get_project_dir(project_id)

            result = subprocess.run(
                ["git", "pull", "origin", branch],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                logger.info(f"✅ Pulled from remote")
                return {
                    "status": "success",
                    "message": "Changes pulled from remote",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Pull failed: {result.stderr}",
                }

        except Exception as e:
            logger.error(f"Pull error: {e}")
            return {
                "status": "error",
                "message": str(e),
            }

    async def list_branches(self, project_id: str) -> List[str]:
        """Get list of branches."""
        try:
            project_dir = self._get_project_dir(project_id)

            result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                branches = [b.strip().replace("* ", "") for b in result.stdout.split("\n") if b.strip()]
                return branches
            return []

        except Exception as e:
            logger.error(f"List branches error: {e}")
            return []

    async def checkout_branch(
        self,
        project_id: str,
        branch: str,
    ) -> Dict[str, str]:
        """
        Checkout a branch.

        Args:
            project_id: Project ID
            branch: Branch name

        Returns:
            Result with status
        """
        try:
            project_dir = self._get_project_dir(project_id)

            result = subprocess.run(
                ["git", "checkout", branch],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                logger.info(f"✅ Checked out branch: {branch}")
                return {
                    "status": "success",
                    "message": f"Checked out {branch}",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Checkout failed: {result.stderr}",
                }

        except Exception as e:
            logger.error(f"Checkout error: {e}")
            return {
                "status": "error",
                "message": str(e),
            }

    async def get_status(self, project_id: str) -> Dict:
        """Get git status."""
        try:
            project_dir = self._get_project_dir(project_id)

            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )

            modified_files = [line for line in result.stdout.split("\n") if line.strip()]

            # Get current branch
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )
            current_branch = branch_result.stdout.strip()

            return {
                "current_branch": current_branch,
                "modified_files": modified_files,
                "has_changes": len(modified_files) > 0,
            }

        except Exception as e:
            logger.error(f"Status error: {e}")
            return {
                "error": str(e),
            }


# Global git service instance
git_service = GitService()
