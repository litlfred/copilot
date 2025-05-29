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
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class GoGoCopilotError(Exception):
    pass


class GoGoCopilot:
    def __init__(self):
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
        return shutil.which("gh") is not None

    def _is_gh_copilot_installed(self) -> bool:
        try:
            output = subprocess.check_output(["gh", "extension", "list"], text=True)
            return "copilot" in output
        except Exception:
            return False

    def _is_gh_authenticated(self) -> bool:
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

    def get_open_issues(self, org: str, repo_name: str) -> List[Tuple[int, str]]:
        """
        Fetch all open issues for the specified repository using gh CLI.
        Returns a list of tuples: (issue_number, issue_title)
        """
        try:
            # Use the GitHub CLI to list issues, outputting number and title
            result = subprocess.check_output(
                [
                    "gh", "issue", "list",
                    "--repo", f"{org}/{repo_name}",
                    "--state", "open",
                    "--json", "number,title"
                ],
                text=True,
            )
            import json
            issues = json.loads(result)
            return [(issue["number"], issue["title"]) for issue in issues]
        except Exception as e:
            raise GoGoCopilotError(f"Failed to fetch issues: {e}")

    def select_issue_ui(self, org: str, repo_name: str) -> Optional[int]:
        """
        Presents a selection menu for all open issues in the repo.
        Returns the selected issue number, or None if cancelled.
        """
        issues = self.get_open_issues(org, repo_name)
        if not issues:
            logging.info("No open issues found.")
            return None
        print("\nSelect an issue:")
        for idx, (num, title) in enumerate(issues, start=1):
            print(f"{idx}. #{num}: {title}")
        while True:
            choice = input(f"\nEnter number (1-{len(issues)}) or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                return None
            if choice.isdigit() and 1 <= int(choice) <= len(issues):
                return issues[int(choice)-1][0]
            print("Invalid selection. Try again.")

    def run_issue_solution_flow(self, org: str, repo_name: str):
        """
        High-level flow:
        1. Fetch issues for repo.
        2. Prompt user to select one.
        3. Request Copilot to suggest a solution for the selected issue.
        4. Display Copilot's explanation and proposed files.
        """
        issue_num = self.select_issue_ui(org, repo_name)
        if issue_num is None:
            print("No issue selected. Exiting.")
            return
        print(f"\nRequesting Copilot suggestion for issue #{issue_num}...\n")
        try:
            result = self.suggest_solution(org, repo_name, issue_num)
            print("\n--- Copilot Explanation ---\n")
            print(result["explanation"])
            if result["files"]:
                print("\n--- Copilot Proposed Files ---\n")
                for fname, fcontent in result["files"].items():
                    print(f"\nFile: {fname}\n{'-'*len(fname)}\n{fcontent}\n")
            else:
                print("\n(No files proposed.)\n")
        except GoGoCopilotError as e:
            print(f"Error: {e}")