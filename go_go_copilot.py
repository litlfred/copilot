import subprocess
import logging
import shutil
import re
import os
from typing import Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

class GoGoCopilotError(Exception):
    pass

class GoGoCopilot:
    # ... other methods unchanged ...

    def suggest_solution(
        self, org: str, repo_name: str, issue_num: int
    ) -> Dict[str, object]:
        """
        Requests a Copilot suggestion for a GitHub issue, fully non-interactive.
        """
        prompt = (
            f"Please review the issue at @{org}/{repo_name}/issue/{issue_num} including all of the comments. "
            f"Examine the contents of branch copilot-proposed-fixes-for-issue-{issue_num} of the repo at {org}/{repo_name} exists, "
            "and use it as a basis for a proposed or modified solution to the issue. "
            "The proposed solution should include an EXPLANATION of the approach and any files needed to implement the proposed solution."
        )
        logging.info(f"Requesting solution from Copilot for {org}/{repo_name} issue #{issue_num}")

        env = os.environ.copy()
        env["GH_COPILOT_NO_USAGE_STATS_PROMPT"] = "1"
        env["GH_COPILOT_INTERACTIVE"] = "false"

        # Pass --type code so CLI does not prompt for a mode
        command = [
            "gh", "copilot", "suggest",
            "--type", "code",  # or "explain", "test", or your desired mode
            "--no-interactive",  # if your gh copilot version supports it
        ]

        try:
            # Use DEVNULL for stdin so it cannot prompt even if it tries
            result = subprocess.check_output(
                command,
                input=prompt,
                text=True,
                stderr=subprocess.STDOUT,
                env=env,
                stdin=subprocess.DEVNULL,
            )
            explanation, files = self._parse_copilot_output(result)
            return {"explanation": explanation, "files": files}
        except subprocess.CalledProcessError as e:
            raise GoGoCopilotError(f"Failed to get solution from Copilot: {e.output.strip()}")
        except Exception as e:
            raise GoGoCopilotError(f"Failed to get solution from Copilot: {e}")

    # ... rest of the code unchanged ...