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
from typing import Dict

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
    ) -> Dict[str, object]:
        """
        Asks GitHub Copilot to suggest a solution for a GitHub issue.
        Returns a dict with keys 'explanation' and 'files'.
        Uses stdin to pass the prompt to `gh copilot suggest` due to known CLI limitations.
        """
        prompt = (
            f"Please review the issue at @{org}/{repo_name}/issue/{issue_num} including all of the comments. "
            f"Examine the contents of branch copilot-proposed-fixes-for-issue-{issue_num} of the repo at {org}/{repo_name} exists, "
            "and use it as a basis for a proposed or modified solution to the issue. "
            "The proposed solution should include an EXPLANATION of the approach and any files needed to implement the proposed solution."
        )
        logging.info(f"Requesting solution from Copilot for {org}/{repo_name} issue #{issue_num}")
        try:
            # Pass prompt via stdin, capture output as plain text (markdown)
            result = subprocess.check_output(
                ["gh", "copilot", "suggest"],
                input=prompt,
                text=True,
                stderr=subprocess.STDOUT,
            )
            # Parse output for explanation and files (expect markdown with code blocks)
            explanation, files = self._parse_copilot_output(result)
            return {"explanation": explanation, "files": files}
        except subprocess.CalledProcessError as e:
            raise GoGoCopilotError(f"Failed to get solution from Copilot: {e.output.strip()}")
        except Exception as e:
            raise GoGoCopilotError(f"Failed to get solution from Copilot: {e}")

    def _parse_copilot_output(self, output: str):
        """
        Very basic parser for Copilot markdown output.
        Extracts an explanation (first non-code content) and code blocks as files.
        Expects code blocks in the format: ```filename.ext\n...code...\n```
        """
        explanation_lines = []
        files = {}
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