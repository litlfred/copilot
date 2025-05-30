import subprocess
import json

import logging

from typing import List, Optional, Any


class GitHubManager:
  """Manager for GitHub user, org, and repository information using the gh CLI."""

  def __init__(self) -> None:
    """Initialize GitHubManager and get authenticated username."""
    self.username: Optional[str] = self.get_authenticated_username()
    logging.info(f"Authenticated as GitHub user: {self.username}")

  def _run_gh_command(self, args: List[str]) -> Any:
    """Run a GitHub CLI command and return parsed JSON output.

    Args:
        args (list): Arguments for the gh CLI.

    Returns:
        Any: Parsed JSON output or empty list on failure.
    """
    cmd = ["gh"] + args + ["--json", "name,login"]
    logging.info(f"Running command: {' '.join(cmd)}")
    try:
      result = subprocess.run(cmd, capture_output=True, text=True, check=True)
      return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
      logging.error(f"Command failed: {' '.join(cmd)}")
      logging.error(f"Error output: {e.stderr.strip()}")
      return []
    except Exception as ex:
      logging.error(f"Unexpected error running gh: {ex}")
      return []

  def get_authenticated_username(self) -> Optional[str]:
    """Return the username of the authenticated user.

    Returns:
        str: Authenticated username, or None if not found.
    """
    cmd = ["gh", "api", "user", "--jq", ".login"]
    logging.info(f"Retrieving authenticated username via: {' '.join(cmd)}")
    try:
      result = subprocess.run(cmd, capture_output=True, text=True, check=True)
      return result.stdout.strip()
    except subprocess.CalledProcessError as e:
      logging.error(f"Failed to get authenticated username: {e.stderr.strip()}")
      return None

  def get_user_organizations(self) -> List[str]:
    """Return a list of organization logins the user belongs to.

    Returns:
        list: Organization logins.
    """
    cmd = ["gh", "api", "user/orgs", "--jq", ".[].login"]
    logging.info(f"Retrieving user organizations via: {' '.join(cmd)}")
    try:
      result = subprocess.run(cmd, capture_output=True, text=True, check=True)
      orgs = result.stdout.strip().split('\n')
      orgs = [org for org in orgs if org]
      return orgs
    except subprocess.CalledProcessError as e:
      logging.error(f"Failed to get organizations: {e.stderr.strip()}")
      return []

  def get_repos(self, org_or_user: str) -> List[str]:
    """Return a list of repository names for the given org or user.

    Tries org repos first, falls back to user repos if org fails.

    Args:
        org_or_user (str): Organization or user.

    Returns:
        list: Repository names.
    """
    cmd = ["gh", "repo", "list", f"{org_or_user}", "--limit", "1000", "--json", "name"]
    logging.info(f"Retrieving repositories for '{org_or_user}' via: {' '.join(cmd)}")
    try:
      result = subprocess.run(cmd, capture_output=True, text=True, check=True)
      repo_objs = json.loads(result.stdout)
      repos = [repo['name'] for repo in repo_objs if 'name' in repo]
      return repos
    except subprocess.CalledProcessError as e:
      logging.warning(f"Failed to get repos for org '{org_or_user}': {e.stderr.strip()}")
      if org_or_user == self.username:
        cmd = ["gh", "repo", "list", "--limit", "1000", "--json", "name"]
        try:
          result = subprocess.run(cmd, capture_output=True, text=True, check=True)
          repo_objs = json.loads(result.stdout)
          repos = [repo['name'] for repo in repo_objs if 'name' in repo]
          return repos
        except Exception as ex:
          logging.error(f"Failed to get user repos: {ex}")
          return []
      else:
        return []
    except Exception as ex:
      logging.error(f"Unexpected error running gh: {ex}")
      return []

  @property
  def user(self) -> Optional[str]:
    """Get the username (for compatibility with config_ui.py).

    Returns:
        str: Authenticated username.
    """
    return self.username