Module gogo_git
===============
gogo-git.py

Author: Copilot (GitHub Copilot, OpenAI, and contributors)
Attribution: Generated with the help of GitHub Copilot and OpenAI's GPT models. Thanks to the authors of GitPython and the open-source community.

An object-oriented, importable Python module for managing git repositories, executing git commands with logging, 
and now also managing checks for gh CLI and Copilot CLI.

Classes
-------

`GoGoGit(repo_path: str)`
:   

    ### Static methods

    `is_gh_authenticated() ‑> bool`
    :

    `is_gh_copilot_installed() ‑> bool`
    :

    `is_gh_installed() ‑> bool`
    :

    `is_git_installed() ‑> bool`
    :

    ### Methods

    `add_commit_push(self, files: List[str], message: str, push: bool = False)`
    :   Add files, commit with message, and optionally push to origin.

    `apply_patch(self, patch_file)`
    :   Apply a patch file to the repository using git apply.

    `assert_gh_ready(self)`
    :

    `branch_exists(self, branch: str) ‑> bool`
    :

    `ensure_cloned(self, org: str, repo_name: str, base_dir: str) ‑> str`
    :   Ensure that DIR/org/repo_name exists as a git repo, cloning if necessary.

    `is_clean(self) ‑> bool`
    :   Check if the repository is clean (no uncommitted changes).

    `is_git_repo(self) ‑> bool`
    :

    `switch_or_create_branch(self, branch: str, push: bool = False)`
    :   Switch to a branch, or create it (and optionally push to origin) if it doesn't exist.

`GoGoGitError(*args, **kwargs)`
:   Common base class for all non-exit exceptions.

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException