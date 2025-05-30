import logging
import os
import subprocess
from gogo_git import GoGoGit
from gogo_structuredproposalresponse import StructuredProposalResponse, StructuredProposalResponseError

class GoGoCopilotError(Exception):
    pass

class GoGoCopilot:
    def __init__(self, preamble_path="prompts/preamble.md", postamble_path="prompts/postamble.md"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing GoGoCopilot instance.")
        self._check_gh_and_copilot()
        self.preamble = self._load_file(preamble_path)
        self.postamble = self._load_file(postamble_path)

    def _check_gh_and_copilot(self):
        self.logger.debug("Checking for gh CLI installation.")
        result = subprocess.run(["gh", "--version"], capture_output=True)
        if result.returncode != 0:
            self.logger.error("gh CLI not found.")
            raise GoGoCopilotError("gh CLI is not installed.")
        self.logger.info("gh CLI is installed.")
        self.logger.debug("Checking for gh copilot extension.")
        result = subprocess.run(["gh", "extension", "list"], capture_output=True, text=True)
        if "copilot" not in result.stdout:
            self.logger.error("gh copilot extension not installed.")
            raise GoGoCopilotError("gh copilot extension is not installed.")
        self.logger.info("gh copilot extension is installed.")

    def _load_file(self, path):
        self.logger.debug(f"Loading file at path: {path}")
        if os.path.exists(path):
            with open(path, "r") as f:
                content = f.read()
            self.logger.info(f"Loaded file: {path}")
            return content
        self.logger.warning(f"File not found: {path}. Using empty string.")
        return ""

    def get_preamble(self):
        self.logger.debug("Getting preamble string.")
        return self.preamble

    def set_preamble(self, text):
        self.logger.info("Setting new preamble string.")
        self.preamble = text

    def get_postamble(self):
        self.logger.debug("Getting postamble string.")
        return self.postamble

    def set_postamble(self, text):
        self.logger.info("Setting new postamble string.")
        self.postamble = text

    def suggest_solution(self, org, repo, issue_num):
        prompt = f"{self.preamble}\nPlease solve {org}/{repo}/issue/{issue_num}\n{self.postamble}"
        self.logger.info(f"Invoking Copilot for solution: org={org}, repo={repo}, issue={issue_num}")
        self.logger.debug(f"Prompt sent to Copilot:\n{prompt}")
        try:
            result = subprocess.run(
                ["gh", "copilot", "suggest", "--prompt", prompt, "--repo", f"{org}/{repo}"],
                capture_output=True,
                text=True,
            )
            self.logger.debug(f"Copilot suggest command exit code: {result.returncode}")
            if result.returncode != 0:
                self.logger.error(f"Copilot suggest failed: {result.stderr}")
                raise GoGoCopilotError("Failed to get Copilot suggestion.")
            self.logger.info("Copilot suggestion received successfully.")
            # Parse result.stdout as StructuredProposalResponse (JSON)
            return StructuredProposalResponse.from_json(result.stdout)
        except Exception as e:
            self.logger.exception("Error during suggest_solution")
            raise GoGoCopilotError(str(e))

    def install_suggestion(self, proposal: StructuredProposalResponse):
        self.logger.info("Installing proposal suggestion.")
        for filename, content in proposal.files.items():
            self.logger.debug(f"Writing file: {filename}")
            with open(filename, "w") as f:
                f.write(content)
            self.logger.info(f"Wrote file: {filename}")
        if proposal.patch:
            self.logger.debug("Applying patch from proposal.")
            patch_proc = subprocess.run(["git", "apply"], input=proposal.patch, text=True, capture_output=True)
            self.logger.debug(f"Patch application exit code: {patch_proc.returncode}")
            if patch_proc.returncode != 0:
                self.logger.error(f"Failed to apply patch: {patch_proc.stderr}")
                raise GoGoCopilotError("Patch application failed.")
            self.logger.info("Patch applied successfully.")