"""
go_go_copilot.py

Author: Copilot (GitHub Copilot, OpenAI, and contributors)
Attribution: Generated with the help of GitHub Copilot and OpenAI's GPT models.
Thanks to the authors of the GitHub CLI and related open-source tools.

An object-oriented, importable Python module for interacting with GitHub Copilot via the `gh` CLI.
"""

import subprocess
import logging
import json
import shutil

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class GoGoCopilotError(Exception):
    pass


class GoGoCopilot:
    def __init__(self):
        if not self._is_gh_installed():
            raise GoGoCopilotError("GitHub CLI (gh) is not installed.")
        if not self._is_gh_copilot_installed():
            raise GoGoCopilotError("GitHub Copilot CLI extension is not installed.")

    def _is_gh_installed(self) -> bool:
        return shutil.which("gh") is not None

    def _is_gh_copilot_installed(self) -> bool:
        try:
            output = subprocess.check_output(["gh", "extension", "list"], text=True)
            return "copilot" in output
        except Exception:
            return False

    def suggest_solution(
        self, org: str, repo_name: str, issue_num: int
    ) -> dict:
        """
        Asks GitHub Copilot to suggest a solution for a GitHub issue.
        Returns a dict with keys 'explanation' and 'files'.
        """
        prompt = (
            f"Please review the issue at @{org}/{repo_name}/issue/{issue_num} including all of the comments. "
            f"Examine the contents of branch copilot-proposed-fixes-for-issue-{issue_num} of the repo at {org}/{repo_name} exists, "
            "and use it as a basis for a proposed or modified solution to the issue. "
            "The proposed solution should include an EXPLANATION of the approach and any files needed to implement the proposed solution."
        )
        logging.info(f"Requesting solution from Copilot for {org}/{repo_name} issue #{issue_num}")
        try:
            # This assumes a Copilot CLI interface that can take prompt and output JSON
            result = subprocess.check_output(
                [
                    "gh",
                    "copilot",
                    "suggest",
                    "--repo",
                    f"{org}/{repo_name}",
                    "--issue",
                    str(issue_num),
                    "--prompt",
                    prompt,
                    "--json"
                ],
                text=True,
            )
            data = json.loads(result)
            explanation = data.get("explanation", "")
            files = data.get("files", {})
            return {"explanation": explanation, "files": files}
        except Exception as e:
            raise GoGoCopilotError(f"Failed to get solution from Copilot: {e}")