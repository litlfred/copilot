"""
go_go_copilot.py

Author: Copilot (GitHub Copilot, OpenAI, and contributors)
Attribution: Generated with the help of GitHub Copilot and OpenAI's GPT models.
Thanks to the authors of the GitHub CLI and related open-source tools.

An object-oriented, importable Python module for interacting with GitHub Copilot via the `gh` CLI.
"""

import subprocess
import logging
import shutil
import re

from typing import Dict, Any, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class GoGoCopilotError(Exception):
  """Exception for GoGoCopilot-related errors."""
  pass


class GoGoCopilot:
  """Python interface to interact with GitHub Copilot via the CLI."""

  def __init__(self) -> None:
    """Initialize GoGoCopilot and check dependencies/authentication."""
    if not self._is_gh_installed():
      raise GoGoCopilotError("GitHub CLI (gh) is not installed.")
    if not self._is_gh_copilot_installed():
      raise GoGoCopilotError("GitHub Copilot CLI extension is not installed.")
    if not self._is_gh_authenticated():
      raise GoGoCopilotError(
        "No valid GitHub CLI access token detected.\n\n"
        "To use GitHub Copilot in the CLI, you must authenticate the GitHub CLI using a personal access token (PAT).\n"
        "Follow these steps:\n"
        "1. Visit https://github.com/settings/tokens?type=beta\n"
        "2. Generate a new fine-grained personal access token with these scopes: 'repo', 'read:org', and 'copilot'.\n"
        "3. Save the token into a file, e.g. 'token.txt'.\n"
        "4. Authenticate with the GitHub CLI by running:\n"
        "     gh auth login --with-token < token.txt\n"
        "5. After authenticating, re-run this script.\n"
        "For more info, see: https://cli.github.com/manual/gh_auth_login\n"
      )

  def _is_gh_installed(self) -> bool:
    """Check if the GitHub CLI is installed.

    Returns:
        bool: True if gh is installed.
    """
    return shutil.which("gh") is not None

  def _is_gh_copilot_installed(self) -> bool:
    """Check if the Copilot CLI extension is installed.

    Returns:
        bool: True if Copilot CLI extension is installed.
    """
    try:
      output = subprocess.check_output(["gh", "extension", "list"], text=True)
      return "copilot" in output
    except Exception:
      return False

  def _is_gh_authenticated(self) -> bool:
    """Check if the GitHub CLI is authenticated.

    Returns:
        bool: True if authenticated.
    """
    try:
      result = subprocess.run(
        ["gh", "auth", "status"],
        capture_output=True,
        text=True,
        check=True,
      )
      return "Logged in to github.com" in result.stdout
    except subprocess.CalledProcessError:
      return False

  def suggest_solution(
    self, org: str, repo_name: str, issue_num: int
  ) -> Dict[str, Any]:
    """Ask GitHub Copilot to suggest a solution for a GitHub issue.

    Args:
        org (str): GitHub organization.
        repo_name (str): GitHub repository.
        issue_num (int): GitHub issue number.

    Returns:
        dict: Dict with keys 'explanation' and 'files'.
    """
    prompt = (
      f"Please review the issue at @{org}/{repo_name}/issue/{issue_num} including all of the comments. "
      f"Examine the contents of branch copilot-proposed-fixes-for-issue-{issue_num} of the repo at {org}/{repo_name} exists, "
      "and use it as a basis for a proposed or modified solution to the issue. "
      "The proposed solution should include an EXPLANATION of the approach and any files needed to implement the proposed solution."
    )
    logging.info(f"Requesting solution from Copilot for {org}/{repo_name} issue #{issue_num}")
    try:
      result = subprocess.check_output(
        ["gh", "copilot", "suggest"],
        input=prompt,
        text=True,
        stderr=subprocess.STDOUT,
      )
      explanation, files = self._parse_copilot_output(result)
      return {"explanation": explanation, "files": files}
    except subprocess.CalledProcessError as e:
      raise GoGoCopilotError(f"Failed to get solution from Copilot: {e.output.strip()}")
    except Exception as e:
      raise GoGoCopilotError(f"Failed to get solution from Copilot: {e}")

  def _parse_copilot_output(self, output: str) -> Tuple[str, Dict[str, str]]:
    """Very basic parser for Copilot markdown output.

    Extracts an explanation (first non-code content) and code blocks as files.
    Expects code blocks in the format: ```filename.ext\n...code...\n```

    Args:
        output (str): Copilot's markdown output.

    Returns:
        tuple: (explanation, files dictionary)
    """
    explanation_lines = []
    files: Dict[str, str] = {}
    cur_file = None
    cur_code = []
    in_code = False
    code_block_re = re.compile(r"^```([^\n]+)")
    lines = output.splitlines()
    for line in lines:
      if not in_code and line.startswith("```"):
        m = code_block_re.match(line)
        if m:
          cur_file = m.group(1).strip()
          cur_code = []
          in_code = True
        else:
          in_code = True
          cur_file = None
          cur_code = []
      elif in_code and line.startswith("```"):
        if cur_file:
          files[cur_file] = "\n".join(cur_code)
        in_code = False
        cur_file = None
        cur_code = []
      elif in_code:
        cur_code.append(line)
      elif not in_code:
        explanation_lines.append(line)
    explanation = "\n".join(explanation_lines).strip()
    if not files and not explanation:
      explanation = output.strip()
    return explanation, files