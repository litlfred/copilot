"""
go_go_copilot.py

Refactored: integrates Copilot with config_ui.py menus and go_go_git.py for repo and gh checks.
All gh/git/Copilot CLI checks now use GoGoGit.
"""

import subprocess
import logging
import re
import os
from typing import Dict, Optional
from config_ui import ConfigUi
from go_go_git import GoGoGit, GoGoGitError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

class GoGoCopilotError(Exception):
    pass

class GoGoCopilot:
    def __init__(self):
        # Delegate all checks to GoGoGit
        GoGoGit.assert_gh_ready()

    def suggest_solution(
        self, org: str, repo_name: str, issue_num: int, repo_base_dir: Optional[str] = None
    ) -> Dict[str, object]:
        """
        Asks GitHub Copilot to suggest a solution for a GitHub issue.
        Ensures repo is cloned using GoGoGit before invoking Copilot.
        """
        # Ensure repo is present locally
        if repo_base_dir is not None:
            repo_path = GoGoGit.ensure_cloned(org, repo_name, repo_base_dir)
        else:
            repo_path = os.getcwd()
        logging.info(f"Working in repo path: {repo_path}")

        prompt = (
            f"Please review the issue at @{org}/{repo_name}/issue/{issue_num} including all of the comments. "
            f"Examine the contents of branch copilot-proposed-fixes-for-issue-{issue_num} of the repo at {org}/{repo_name} if it exists, "
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
                cwd=repo_path,
            )
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

class CopilotMenu(ConfigUi):
    def __init__(self, configFilePath='config.json', appName='CopilotConfigUI'):
        super().__init__(configFilePath, appName)
        self.copilot = GoGoCopilot()

    def topLevelMenu(self):
        while True:
            result = self._button_dialog(
                title=self.appName,
                text="Select a menu:",
                buttons=[
                    ("GitHub Org & User", "org_user"),
                    ("Copilot", "copilot"),
                    ("Exit", "exit"),
                ]
            )
            if result == "org_user":
                self.orgUserMenu()
            elif result == "copilot":
                self.copilotMenu()
            elif result == "exit":
                logging.info("Exiting application.")
                break

    def copilotMenu(self):
        orgs = self.githubManager.get_user_organizations()
        user = self._getAuthenticatedUsername()
        choices = [(org, org) for org in orgs]
        choices.append((user, user))
        orgOrUser = self._radiolist_dialog(
            title="Copilot - Org/User",
            text="Select an organization or your username:",
            values=choices
        )
        if not orgOrUser:
            return
        repos = self.githubManager.get_repos(orgOrUser)
        repo = self._radiolist_dialog(
            title="Copilot - Repo",
            text="Select a repository:",
            values=[(r, r) for r in repos]
        )
        if not repo:
            return
        issue_num = self._input_dialog(
            title="Copilot - Issue Number",
            text="Enter the GitHub issue number to solve:"
        )
        if not issue_num or not issue_num.isdigit():
            logging.warning("Invalid issue number.")
            return
        issue_num = int(issue_num)
        repo_base_dir = os.path.expanduser("~/copilot_repos")
        try:
            result = self.copilot.suggest_solution(orgOrUser, repo, issue_num, repo_base_dir)
            self._display_solution(result)
        except Exception as e:
            logging.error(f"Error running Copilot: {e}")

    # Dialog wrappers to allow easier testing (prompt_toolkit dialogs)
    def _button_dialog(self, title, text, buttons):
        from prompt_toolkit.shortcuts import button_dialog
        return button_dialog(title=title, text=text, buttons=buttons).run()

    def _radiolist_dialog(self, title, text, values):
        from prompt_toolkit.shortcuts import radiolist_dialog
        return radiolist_dialog(title=title, text=text, values=values).run()

    def _input_dialog(self, title, text):
        from prompt_toolkit.shortcuts import input_dialog
        return input_dialog(title=title, text=text).run()

    def _display_solution(self, result: dict):
        explanation = result.get("explanation", "")
        files = result.get("files", {})
        print("\n==== Copilot Solution ====")
        print(explanation)
        for fn, code in files.items():
            print(f"\n--- {fn} ---\n{code}\n")

if __name__ == "__main__":
    ui = CopilotMenu()
    ui.run()