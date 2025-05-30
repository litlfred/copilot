Module github_manager
=====================

Classes
-------

`GitHubManager()`
:   Manager for GitHub user, org, and repository information using the gh CLI.
    
    Initialize GitHubManager and get authenticated username.

    ### Instance variables

    `user: str | None`
    :   Get the username (for compatibility with config_ui.py).
        
        Returns:
            str: Authenticated username.

    ### Methods

    `get_authenticated_username(self) ‑> str | None`
    :   Return the username of the authenticated user.
        
        Returns:
            str: Authenticated username, or None if not found.

    `get_repos(self, org_or_user: str) ‑> List[str]`
    :   Return a list of repository names for the given org or user.
        
        Tries org repos first, falls back to user repos if org fails.
        
        Args:
            org_or_user (str): Organization or user.
        
        Returns:
            list: Repository names.

    `get_user_organizations(self) ‑> List[str]`
    :   Return a list of organization logins the user belongs to.
        
        Returns:
            list: Organization logins.