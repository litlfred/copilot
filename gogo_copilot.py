import logging
import os
import subprocess
from typing import Optional

from git import Repo, GitCommandError

from gogo_structuredproposalresponse import StructuredProposalResponse, StructuredProposalResponseError

class GoGoCopilotError(Exception):
    pass

class GoGoCopilot:
    def __init__(self, preamble_path="prompts/preamble.md", postamble_path="prompts/postamble.md", repo_path: Optional[str] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing GoGoCopilot instance.")
        self._check_gh_and_copilot()
        self.preamble = self._load_file(preamble_path)
        self.postamble = self._load_file(postamble_path)
        self.repo_path = repo_path or os.getcwd()
        try:
            self.repo = Repo(self.repo_path)
        except Exception as e:
            self.logger.error(f"Could not initialize git repo at {self.repo_path}: {e}")
            self.repo = None

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
        # Refactored to use only 'patch' field and GitPython
        try:
            if not self.repo:
                raise GoGoCopilotError("Git repo is not initialized.")
            if not proposal.patch:
                self.logger.error("No patch found in proposal.")
                raise GoGoCopilotError("Proposal does not contain a patch.")
            self.logger.debug("Applying patch from proposal using GitPython.")
            try:
                # GitPython's git interface allows you to pass the patch via stdin using '--whitespace=nowarn' for leniency if needed
                self.repo.git.apply('--whitespace=nowarn', with_stdout=False, input=proposal.patch)
                self.logger.info("Patch applied successfully using GitPython.")
            except GitCommandError as gce:
                self.logger.error(f"Failed to apply patch via GitPython: {gce}")
                raise GoGoCopilotError(f"Patch application failed: {gce}")
        except Exception as e:
            self.logger.exception("Error in install_suggestion")
            raise GoGoCopilotError(str(e))

    def add_proposal(self, srp: StructuredProposalResponse, interactive: bool = False):
        """
        Add files from proposal's patch to git staging area. Optionally in interactive mode,
        prompt to add unstaged files. Always stages conversation.GoGoCopilot.md if present.
        """
        self.logger.info("Adding proposal files to git staging.")
        if not self.repo:
            raise GoGoCopilotError("Git repo is not initialized.")
        if not srp.patch:
            self.logger.error("No patch found in proposal.")
            raise GoGoCopilotError("Proposal does not contain a patch.")
        try:
            # Parse patch to get changed file paths
            changed_files = self._parse_patch_files(srp.patch)
            if not changed_files:
                self.logger.warning("No changed files detected in patch.")
            for path in changed_files:
                self.logger.debug(f"Staging file: {path}")
                try:
                    self.repo.git.add(path)
                except GitCommandError as gce:
                    self.logger.error(f"Failed to add {path}: {gce}")
                    raise GoGoCopilotError(f"Failed to stage {path}: {gce}")

            # Always check for conversation.GoGoCopilot.md and stage if present
            conv_file = "conversation.GoGoCopilot.md"
            conv_path = os.path.join(self.repo.working_tree_dir, conv_file)
            if os.path.exists(conv_path):
                try:
                    self.logger.info(f"Staging {conv_file}.")
                    self.repo.git.add(conv_file)
                except GitCommandError as gce:
                    self.logger.error(f"Failed to add {conv_file}: {gce}")
                    raise GoGoCopilotError(f"Failed to stage {conv_file}: {gce}")

            if interactive:
                unstaged = [item.a_path for item in self.repo.index.diff(None)]
                if unstaged:
                    self.logger.info(f"Unstaged files detected: {unstaged}")
                    print("Unstaged files detected:")
                    for idx, fname in enumerate(unstaged, 1):
                        print(f"{idx}: {fname}")
                    print('Enter "all" to stage all, "none" to skip, or a comma-separated list of numbers to stage particular files.')
                    ans = input("Your choice: ").strip().lower()
                    to_stage = []
                    if ans == "all":
                        to_stage = unstaged
                    elif ans == "none" or ans == "":
                        to_stage = []
                    else:
                        try:
                            indices = [int(i) for i in ans.split(",") if i.strip().isdigit()]
                            to_stage = [unstaged[i - 1] for i in indices if 0 < i <= len(unstaged)]
                        except Exception as e:
                            self.logger.error(f"Error parsing selection: {e}")
                            raise GoGoCopilotError("Invalid selection for staging files.")
                    for path in to_stage:
                        try:
                            self.repo.git.add(path)
                            self.logger.info(f"Staged unstaged file: {path}")
                        except GitCommandError as gce:
                            self.logger.error(f"Failed to add {path}: {gce}")
                            raise GoGoCopilotError(f"Failed to stage {path}: {gce}")
        except Exception as e:
            self.logger.exception("Error in add_proposal")
            raise GoGoCopilotError(str(e))

    def commit_proposal(self, srp: StructuredProposalResponse):
        """
        Commit the staged files with the commit message from srp.message.
        """
        self.logger.info("Committing proposal to git.")
        if not self.repo:
            raise GoGoCopilotError("Git repo is not initialized.")
        if not srp.message:
            self.logger.error("No commit message found in proposal.")
            raise GoGoCopilotError("Proposal does not contain a commit message.")
        try:
            commit = self.repo.index.commit(srp.message)
            self.logger.info(f"Committed with: {commit.hexsha}")
        except Exception as e:
            self.logger.error(f"Failed to commit: {e}")
            raise GoGoCopilotError(f"Failed to commit: {e}")

    def _parse_patch_files(self, patch: str):
        """
        Parse a unified diff patch and return a set of changed file paths.
        """
        files = set()
        for line in patch.splitlines():
            if line.startswith('+++ b/'):
                path = line[6:]
                if path != '/dev/null':
                    files.add(path)
        self.logger.debug(f"Files parsed from patch: {files}")
        return files