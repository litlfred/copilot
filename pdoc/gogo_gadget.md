Module gogo_gadget
==================

Classes
-------

`GoGoGadget()`
:   

    ### Methods

    `install_suggestion(self, structured_response: Dict[str, Any], target_dir: str) ‑> None`
    :   Copy the proposed solution files from the processed structured response to a named directory.

    `process_structured_response(self, suggestion: str) ‑> Dict[str, Any]`
    :   Parse a "Structured Response" from Copilot suggestion as per the specification.
        Returns a python dict.

    `suggest_solution(self, org: str, repo_name: str, issue_num: int) ‑> Dict[str, object]`
    :   Requests a Copilot suggestion for a GitHub issue, fully non-interactive.

`GoGoGadgetError(*args, **kwargs)`
:   Common base class for all non-exit exceptions.

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException