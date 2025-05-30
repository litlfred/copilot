Module gogo-copilot
===================

Classes
-------

`GoGoCopilot()`
:   

    ### Methods

    `suggest_solution(self, org: str, repo_name: str, issue_num: int) ‑> Dict[str, object]`
    :   Requests a Copilot suggestion for a GitHub issue, fully non-interactive.

`GoGoCopilotError(*args, **kwargs)`
:   Common base class for all non-exit exceptions.

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException