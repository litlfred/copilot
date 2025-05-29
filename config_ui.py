import json
import os

import logging

from typing import Optional, Dict, Any, List

from github_manager import GitHubManager

try:
  from prompt_toolkit.shortcuts import checkboxlist_dialog, button_dialog, radiolist_dialog
except ImportError:
  raise ImportError("Install prompt_toolkit: pip install prompt_toolkit")

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')


class ConfigUi:
  """Configuration UI for managing enabled repositories."""

  def __init__(self, configFilePath: str = 'config.json', appName: str = 'CopilotConfigUI') -> None:
    """Initialize ConfigUi.

    Args:
        configFilePath (str): Path to the config file.
        appName (str): Application name.
    """
    self.configFilePath = configFilePath
    self.appName = appName
    self.githubManager = GitHubManager()
    self.config = self.loadConfig()
    logging.info(f"Initialized {self.appName} with config file: {self.configFilePath}")

  def loadConfig(self) -> Dict[str, Any]:
    """Load configuration from file or create default config.

    Returns:
        dict: Configuration dictionary.
    """
    if not os.path.exists(self.configFilePath):
      logging.info(f"Config file {self.configFilePath} not found. Creating default config.")
      config = {'enabled_repos': []}
      self.saveConfig(config)
    else:
      with open(self.configFilePath, 'r') as f:
        config = json.load(f)
      if 'enabled_repos' not in config:
        config['enabled_repos'] = []
    return config

  def saveConfig(self, config: Optional[Dict[str, Any]] = None) -> None:
    """Save configuration to file.

    Args:
        config (dict, optional): Configuration to save. Defaults to self.config.
    """
    config = config or self.config
    with open(self.configFilePath, 'w') as f:
      json.dump(config, f, indent=2)
    logging.info(f"Saved configuration to {self.configFilePath}")

  def run(self) -> None:
    """Run the top-level menu."""
    self.topLevelMenu()

  def _getAuthenticatedUsername(self) -> str:
    """Get the authenticated GitHub username.

    Returns:
        str: Authenticated username.

    Raises:
        AttributeError: If username method/property not found.
    """
    if hasattr(self.githubManager, 'get_authenticated_username'):
      return self.githubManager.get_authenticated_username()
    if hasattr(self.githubManager, 'get_username'):
      return self.githubManager.get_username()
    if hasattr(self.githubManager, 'username'):
      return self.githubManager.username
    if hasattr(self.githubManager, 'user'):
      return self.githubManager.user
    logging.error(
      "Could not find a method to get the authenticated username in GitHubManager. "
      "Please implement get_authenticated_username(), get_username(), or a .username property."
    )
    raise AttributeError(
      "GitHubManager object has no method or property for the authenticated username."
    )

  def topLevelMenu(self) -> None:
    """Display the top-level menu."""
    while True:
      result = button_dialog(
        title=self.appName,
        text="Select a menu:",
        buttons=[
          ("GitHub Org & User", "org_user"),
          ("Exit", "exit")
        ]
      ).run()
      if result == "org_user":
        self.orgUserMenu()
      elif result == "exit":
        logging.info("Exiting application.")
        break

  def orgUserMenu(self) -> None:
    """Display the organization/user selection menu."""
    orgs = self.githubManager.get_user_organizations()
    user = self._getAuthenticatedUsername()
    choices: List[tuple] = [(org, org) for org in orgs]
    choices.append((user, user))
    while True:
      result = radiolist_dialog(
        title="GitHub Org & User Menu",
        text="Select an organization or your username:",
        values=choices + [("back", "< Back to Top-Level Menu>")]
      ).run()
      if result == "back" or result is None:
        logging.info("Returning to Top-Level menu.")
        return
      else:
        self.repositoryMenu(result)

  def repositoryMenu(self, orgOrUser: str) -> None:
    """Display the repository enable/disable menu for a selected org/user.

    Args:
        orgOrUser (str): Organization or user name.
    """
    repos = self.githubManager.get_repos(orgOrUser)
    enabledSet = {(r['org'], r['repo_name']) for r in self.config['enabled_repos']}
    while True:
      choices = [(repo, repo) for repo in repos]
      defaultValues = [repo for repo in repos if (orgOrUser, repo) in enabledSet]
      result = checkboxlist_dialog(
        title=f"Repositories for {orgOrUser}",
        text="Enable/disable repositories:",
        values=choices + [("back", "< Back to Org/User Menu>")],
        default_values=defaultValues,
        ok_text="Apply",
        cancel_text="Back"
      ).run()
      if result is None or "back" in result:
        logging.info("Returning to Org/User menu.")
        return
      self.config['enabled_repos'] = [
        r for r in self.config['enabled_repos']
        if r['org'] != orgOrUser
      ]
      for repo in result:
        if repo != "back":
          self.config['enabled_repos'].append({'org': orgOrUser, 'repo_name': repo})
          logging.info(f"Enabled repo {repo} for {orgOrUser}")
      self.saveConfig()
      enabledSet = {(r['org'], r['repo_name']) for r in self.config['enabled_repos']}


if __name__ == '__main__':
  ui = ConfigUi()
  ui.run()