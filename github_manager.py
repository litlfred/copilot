import subprocess
import logging
import os
from typing import List, Optional

class GitHubManagerException(Exception):
  """Custom exception for GitHubManager errors."""
  pass

class GitHubManager:
  """
  Python module to manage interactions with GitHub using git and gh.
  Performs system and configuration checks on initialization.
  """

  def __init__(self, verbose: bool = True):
    """
    Initialize GitHubManager and perform required system checks.
    Raises:
      GitHubManagerException: If required tools or configuration are missing.
    """
    # Configure logging
    self.verbose = verbose
    logging.basicConfig(
      level=logging.DEBUG if self.verbose else logging.INFO,
      format='%(asctime)s [%(levelname)s] %(message)s'
    )
    self.gitUserName: Optional[str] = None
    self.gitUserEmail: Optional[str] = None

    self._check_requirements()
    self.gitUserName = self._get_git_config('user.name')
    self.gitUserEmail = self._get_git_config('user.email')

  def _run_cmd(self, cmd: List[str], cwd: Optional[str] = None) -> str:
    """
    Run a shell command and return output. Logs command and args.
    Raises:
      GitHubManagerException: If command fails.
    """
    logging.debug(f"Running command: {' '.join(cmd)} (cwd={cwd or os.getcwd()})")
    try:
      result = subprocess.run(
        cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
      )
      logging.debug(f"Command output: {result.stdout.strip()}")
      return result.stdout.strip()
    except subprocess.CalledProcessError as e:
      logging.error(f"Command failed: {' '.join(cmd)}\nError: {e.stderr.strip()}")
      raise GitHubManagerException(f"Command failed: {' '.join(cmd)}\n{e.stderr.strip()}")

  def _check_requirements(self) -> None:
    """Check that git and gh are installed and git is configured."""
    # Check git is installed
    self._run_cmd(['git', '--version'])
    # Check gh is installed
    self._run_cmd(['gh', '--version'])
    # Check git config for user.name and user.email
    if not self._get_git_config('user.name') or not self._get_git_config('user.email'):
      raise GitHubManagerException("git user.name and/or user.email not configured")

  def _get_git_config(self, key: str) -> Optional[str]:
    """Retrieve a git config value."""
    try:
      value = self._run_cmd(['git', 'config', '--get', key])
      logging.debug(f"git config {key}: {value}")
      return value
    except GitHubManagerException:
      return None

  def get_user_organizations(self) -> List[str]:
    """
    Retrieve a list of organizations associated with the authenticated user.
    Returns:
      List[str]: List of organization logins.
    """
    logging.info("Retrieving user organizations via gh api")
    output = self._run_cmd(['gh', 'api', 'user/orgs', '--jq', '.[].login'])
    orgs = output.splitlines()
    logging.debug(f"Organizations: {orgs}")
    return orgs

  def get_repos_for_owner(self, owner: str) -> List[str]:
    """
    Retrieve all repos for a given organization or user.
    Args:
      owner (str): Organization or user name.
    Returns:
      List[str]: List of repository names.
    """
    logging.info(f"Retrieving repositories for owner: {owner}")
    output = self._run_cmd([
      'gh', 'repo', 'list', owner, '--json', 'name', '--jq', '.[].name'
    ])
    repos = output.splitlines()
    logging.debug(f"Repositories for {owner}: {repos}")
    return repos

  def clone_repo(self, organization: str, repoName: str) -> None:
    """
    Clone a repo using SSH into organization/repoName directory.
    Args:
      organization (str): Organization name.
      repoName (str): Repository name.
    """
    target_dir = os.path.join(organization, repoName)
    if not os.path.exists(target_dir):
      os.makedirs(os.path.join(organization), exist_ok=True)
    repo_ssh = f'git@github.com:{organization}/{repoName}.git'
    logging.info(f"Cloning {repo_ssh} into {target_dir}")
    self._run_cmd(['git', 'clone', repo_ssh, target_dir])

  def is_git_repo(self, organization: str, repoName: str) -> bool:
    """
    Check if organization/repoName is a git repository.
    Args:
      organization (str): Organization name.
      repoName (str): Repository name.
    Returns:
      bool
    """
    repo_path = os.path.join(organization, repoName)
    git_dir = os.path.join(repo_path, '.git')
    is_repo = os.path.isdir(git_dir)
    logging.info(f"Checking if {repo_path} is a git repo: {is_repo}")
    return is_repo

  def is_repo_clean(self, organization: str, repoName: str) -> bool:
    """
    Check if the repo is in a clean state (no uncommitted changes).
    Args:
      organization (str): Organization name.
      repoName (str): Repository name.
    Returns:
      bool
    """
    repo_path = os.path.join(organization, repoName)
    status = self._run_cmd(['git', 'status', '--porcelain'], cwd=repo_path)
    is_clean = (status == '')
    logging.info(f"Repo {repo_path} clean: {is_clean}")
    return is_clean

  def switch_branch(self, organization: str, repoName: str, branchName: str) -> None:
    """
    Switch to a given branch, creating it if necessary.
    Args:
      organization (str): Organization name.
      repoName (str): Repository name.
      branchName (str): Branch to switch/create.
    """
    repo_path = os.path.join(organization, repoName)
    # Check if branch exists
    branches = self._run_cmd(['git', 'branch', '--list', branchName], cwd=repo_path)
    if not branches:
      logging.info(f"Branch {branchName} does not exist; creating it.")
      self._run_cmd(['git', 'checkout', '-b', branchName], cwd=repo_path)
    else:
      logging.info(f"Switching to branch {branchName}")
      self._run_cmd(['git', 'checkout', branchName], cwd=repo_path)

  def commit_and_optionally_push(
    self, organization: str, repoName: str, files: List[str], commitMsg: str, push: bool = False
  ) -> None:
    """
    Stage, commit, and optionally push files.
    Args:
      organization (str): Organization name.
      repoName (str): Repository name.
      files (List[str]): List of files to add (relative to repo root).
      commitMsg (str): Commit message.
      push (bool): If True, push to origin.
    """
    repo_path = os.path.join(organization, repoName)
    logging.info(f"Staging files: {files} in {repo_path}")
    self._run_cmd(['git', 'add'] + files, cwd=repo_path)
    logging.info(f"Committing with message: {commitMsg}")
    self._run_cmd(['git', 'commit', '-m', commitMsg], cwd=repo_path)
    if push:
      logging.info("Pushing commit to origin")
      self._run_cmd(['git', 'push'], cwd=repo_path)