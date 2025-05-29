# Python Code Style Policy for copilot

This document summarizes the code style guidelines for Python files in the `copilot` project. Please read this carefully before submitting contributions.

## Indentation

- Use **2 spaces** per indentation level (no tabs).

## Logging

- Use the standard Python `logging` module.
- Avoid `print` statements for anything except simple CLI scripts/tests.
- Choose the correct logging level (`debug`, `info`, `warning`, `error`, `critical`).

## Imports

- Order imports as: standard library, third-party, local.
- Separate each import group with a blank line.

## Naming

- Functions and variables: `snake_case`
- Classes: `CamelCase`
- Constants: `UPPER_CASE_WITH_UNDERSCORES`

## Line Length

- Maximum line length: **100 characters**

## Comments and Docstrings

- Public functions and classes must include docstrings.
- Use Google-style docstrings.

## Type Annotations

- All functions should use type annotations for arguments and return types where possible.

## Exceptions

- Raise specific exceptions.
- Never use `except:` without specifying an exception type.

## Object-Oriented Design & Code Reuse

- Favor object-oriented programming (OOP) practices where appropriate.
- Use classes and objects to encapsulate related functionality, encourage code reuse, and enhance maintainability.
- When designing new modules, consider if functionality can be organized into reusable classes or abstracted through base classes and inheritance.
- Avoid duplicating code; refactor common logic into shared methods or classes.

## Use of Git

- All commits should follow clear and descriptive message conventions.
- **Commit messages must indicate which GitHub issue they address or fix, using phrases like "Fixes #12" or "Addresses #34".**
- The commit message should summarize how the commit addresses the referenced issue, describing the specific changes or solutions provided.
- If any code in the commit was developed with the help of an AI model (e.g., GitHub Copilot or ChatGPT), a log of the relevant conversation must be provided and referenced in the commit, ideally as an attachment or link in the commit message. See [attribution guidelines](ATTRIBUTION.md) for more details.

## Clean Code

- Remove unused or commented-out code before submitting.
- Keep functions short and focused.

## Example

```python
import logging

class Calculator:
    """A simple calculator class."""

    def calculate_sum(self, a: int, b: int) -> int:
        """Calculate the sum of two integers.

        Args:
            a (int): First integer.
            b (int): Second integer.

        Returns:
            int: Sum of a and b.
        """
        logging.info("Calculating the sum of %d and %d", a, b)
        return a + b
```