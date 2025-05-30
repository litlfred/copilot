import subprocess
import logging
import shutil
import re
import os
import json
from typing import Dict, Optional, Any

# Corrected import: use underscores, not hyphens, in module names
from gogo_git import GoGoGit, GoGoGitError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

class GoGoGadgetError(Exception):
    pass

class GoGoGadget:
    def __init__(self):
        # Instance variables for consistent prompts
        self.preamble_prompt = self._read_prompt_file("preamble.prompt")
        self.preamble = self._read_prompt_file("prompts/preamble.md")
        self.postamble = self._read_prompt_file("prompts/postamble.md")

    @staticmethod
    def _read_prompt_file(filepath: str) -> str:
        """Read the contents of a prompt file, return empty string if file does not exist."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def _compose_prompt(self, user_prompt: str) -> str:
        """Compose the full prompt with preamble and postamble."""
        return f"{self.preamble_prompt}{self.preamble}\n{user_prompt}\n{self.postamble}"

    def suggest_solution(self, org: str, repo_name: str, issue_num: int) -> Dict[str, object]:
        """
        Requests a Copilot suggestion for a GitHub issue, fully non-interactive.
        """
        user_prompt = (
            f"Please review the issue at @{org}/{repo_name}/issue/{issue_num} including all of the comments. "
            f"Examine the contents of branch copilot-proposed-fixes-for-issue-{issue_num} of the repo at {org}/{repo_name} if it exists, "
            "and use it as a basis for a proposed or modified solution to the issue. "
            "The proposed solution should include an EXPLANATION of the approach and any files needed to implement the proposed solution."
        )
        prompt = self._compose_prompt(user_prompt)
        logging.info(f"Requesting solution from Copilot for {org}/{repo_name} issue #{issue_num}")

        env = os.environ.copy()
        env["GH_COPILOT_NO_USAGE_STATS_PROMPT"] = "1"
        env["GH_COPILOT_INTERACTIVE"] = "false"

        command = [
            "gh", "copilot", "suggest",
            "--type", "code",
            "--no-interactive",
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
            return self.process_structured_response(result)
        except subprocess.CalledProcessError as e:
            raise GoGoGadgetError(f"Failed to get solution from Copilot: {e.output.strip()}")
        except Exception as e:
            raise GoGoGadgetError(f"Failed to get solution from Copilot: {e}")

    def process_structured_response(self, suggestion: str) -> Dict[str, Any]:
        """
        Parse a "Structured Response" from Copilot suggestion as per the specification.
        Returns a python dict.
        """
        try:
            # Try to extract JSON from code blocks if necessary
            match = re.search(r"```json(?P<json>.*?)```", suggestion, re.DOTALL)
            if match:
                json_str = match.group("json")
            else:
                # Fallback: try to parse the whole string
                json_str = suggestion

            # Remove possible leading/trailing whitespace
            json_str = json_str.strip()
            response = json.loads(json_str)
            return response
        except Exception as e:
            logging.error(f"Failed to parse structured response: {e}")
            raise GoGoGadgetError(f"Failed to parse structured response: {e}")

    def install_suggestion(self, structured_response: Dict[str, Any], target_dir: str) -> None:
        """
        Copy the proposed solution files from the processed structured response to a named directory.
        """
        files = structured_response.get("files", {})
        if not files:
            raise GoGoGadgetError("No files found in structured response to install.")

        for rel_path, content in files.items():
            abs_path = os.path.join(target_dir, rel_path)
            abs_dir = os.path.dirname(abs_path)
            os.makedirs(abs_dir, exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            logging.info(f"Installed file: {abs_path}")

        # Optionally, handle install instructions or errors
        if "install" in structured_response:
            logging.info("Manual install instructions: " + str(structured_response["install"]))
        if "errors" in structured_response:
            logging.warning("Errors or warnings: " + str(structured_response["errors"]))

    # ... other methods unchanged ...