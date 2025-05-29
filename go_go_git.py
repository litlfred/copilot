"""
go_go_git.py

Author: Copilot (GitHub Copilot, OpenAI, and contributors)
Attribution: Generated with the help of GitHub Copilot and OpenAI's GPT models. Thanks to the authors of GitPython and the open-source community.

An object-oriented, importable Python module for managing git repositories and executing git commands with logging.
"""

import os
import subprocess
import logging

from typing import List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class GoGoGitError(Exception):
  """Exception for GoGoGit-related errors."""
  pass


class GoGoGit:
  """Class for managing git repositories and executing git commands."""

  def __init__(self, repo_path: str) -> None:
    """Initialize GoGoGit.

    Args:
        repo_path (str): Path to the git repository.

    Raises:
        GoGoGitError: If git is not installed.
    """
    if not self._is_git_installed():
      raise GoGoGitError("git is not installed or not found in PATH.")
    self.repo_path = repo_path
    if not os.path.exists(self.repo_path):
      os.makedirs(self.repo_path, exist_ok=True)
    if not self._is_git_repo():
      logging.info(f"{self.repo_path} is not a git repository.")
    else:
      logging.info(f"Initialized GoGoGit for repository at {self.repo_path}")

  def _is_git_installed(self) -> bool:
    """Check if git is installed.

    Returns:
        bool: True if git is installed.
    """
    try:
      subprocess.check_output(["git", "--version"])
      return True
    except (subprocess.CalledProcessError, FileNotFoundError):
      return False

  def _run_git(self, args: List[str], check: bool = True, capture_output: bool = False) -> subprocess.CompletedProcess:
    """Run a git command.

    Args:
        args (List[str]): Arguments for git.
        check (bool): Whether to check the subprocess result.
        capture_output (bool): Whether to capture output.

    Returns:
        subprocess.CompletedProcess: The process result.
    """
    logging.info(f"Running git command: git {' '.join(args)}")
    return subprocess.run(
      ["git"] + args,
      cwd=self.repo_path,
      check=check,
      capture_output=capture_output,
      text=True
    )

  def _is_git_repo(self) -> bool:
    """Check if the directory is a git repository.

    Returns:
        bool: True if repo_path is a git repository.
    """
    try:
      self._run_git(["rev-parse", "--is-inside-work-tree"], capture_output=True)
      return True
    except subprocess.CalledProcessError:
      return False

  def is_clean(self) -> bool:
    """Check if the repository is clean (no uncommitted changes).

    Returns:
        bool: True if clean.
    """
    result = self._run_git(["status", "--porcelain"], capture_output=True)
    return result.stdout.strip() == ""

  @staticmethod
  def ensure_cloned(org: str, repo_name: str, base_dir: str) -> str:
    """Ensure that DIR/org/repo_name exists as a git repo, cloning if necessary.

    Args:
        org (str): GitHub organization.
        repo_name (str): Repository name.
        base_dir (str): Base directory.

    Returns:
        str: Path to the repository.

    Raises:
        GoGoGitError: If directory exists but is not a git repo.
    """
    repo_path = os.path.join(base_dir, org, repo_name)
    if not os.path.exists(repo_path):
      os.makedirs(os.path.dirname(repo_path), exist_ok=True)
      logging.info(f"Cloning repository {org}/{repo_name} into {repo_path}")
      subprocess.check_call(
        ["git", "clone", f"git@github.com:{org}/{repo_name}.git", repo_path]
      )
    elif not os.path.exists(os.path.join(repo_path, ".git")):
      raise GoGoGitError(f"{repo_path} exists but is not a git repository.")
    return repo_path

  def switch_or_create_branch(self, branch: str, push: bool = False) -> None:
    """Switch to a branch or create it (optionally push to origin) if it doesn't exist.

    Args:
        branch (str): Branch name.
        push (bool): Whether to push to origin.
    """
    try:
      self._run_git(["checkout", branch])
    except subprocess.CalledProcessError:
      logging.info(f"Branch {branch} does not exist. Creating it.")
      self._run_git(["checkout", "-b", branch])
      if push:
        self._run_git(["push", "--set-upstream", "origin", branch])

  def add_commit_push(self, files: List[str], message: str, push: bool = False) -> None:
    """Add files, commit with message, and optionally push to origin.

    Args:
        files (List[str]): List of file names.
        message (str): Commit message.
        push (bool): Whether to push to origin.
    """
    self._run_git(["add"] + files)
    self._run_git(["commit", "-m", message])
    if push:
      self._run_git(["push"])

  def branch_exists(self, branch: str) -> bool:
    """Check if a branch exists.

    Args:
        branch (str): Branch name.

    Returns:
        bool: True if branch exists.
    """
    try:
      self._run_git(["show-ref", "--verify", f"refs/heads/{branch}"], capture_output=True)
      return True
    except subprocess.CalledProcessError:
      return False