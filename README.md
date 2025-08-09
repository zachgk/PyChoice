# PyChoice

A library for manging choices, options, and configurations across abstraction hierarchy
- **Github repository**: <https://github.com/zachgk/PyChoice/>

The pychoice library is a python implementation of choice as described in this [blog post](https://blog.zachkimberg.com/programming%20languages/doing-things-well/) by Zach Kimberg (who also authored this library). The best way to think of pychoice is that it is a pseudo-new feature of the python programming language implemented as a library. It can be used for how to manage complexity around making modules heavily customizable. And this is done by customizing it through the use of choice. This includes customization across abstraction boundaries. Read the original blog post to understand the deeper philosphy behind the language and why it is designed as it is, but this isn't required as the usage is clear enough from examples.

## Library

### Choice Functions

There are two basic types of choices, function choices and argument choices. For a function choice, you begin by creating the function interface:

```python
import pychoice as choice

@choice.func_interface()
def sort(l: list[int]) -> list[int]:
    pass
```

Once you have the general interface, you can begin by adding implementations to it.

```python
@choice.func_impl(sort)
def quicksort(l: list[int]) -> list[int]:
    # Definition here


@choice.func_impl(sort)
def selection_sort(l: list[int]) -> list[int]:
    # Definition here
```

Then, you can begin adding rules to define which implementation to use. These rules can be made to affect choices no matter how deep they are in the call stack. So it can also affect other functions, modules, or even libraries that you are using. The choice rules can define both precise rules for narrow situations or broad rules such as all usages of a library function throughout your code. Multiple conflicting rule are resolved in that the most precise rule takes precedence so it is easy to build them up.

```python
# Least precise rule to act as a default
choice.func_rule([sort], quicksort)

# Updates your user code foo and every indirect usage of sort to override with selection_sort
choice.func_rule([foo, sort], selection_sort)

# Another override of the foo override
choice.func_rule([bar, foo, sort], selection_sort)
```

It is also possible to use this system for code injection. If you define a new implementation for an existing interface such as one provided by a library, this can inject your new implementation in.

### Choice Arguments

The second type is choice arguments which can modify the behavior of functions. Unlike the way standard arguments behave, a choice argument can be changed not just by the parent but by indirect parents. This means you no longer have to have a call stack daisy chain optional arguments down. Nor do you have to define configuration objects to store all of the arguments you want to daisy chain down. This is easy with choice arguments.

You begin by defining the function to accept choice arguments and which arguments to make choices. These should be keyword arguments and have defaults even if the default is `None`:

```python
@choice.args("greeting")
def greet(name: str, greeting="Hello"):
    return f"{greeting} {name}"
```

Now, this greet function will allow customization of the greeting it gives. The default becomes "Hello". Then, you can define the choice rules for the arguments similarly to above:

```python
choice.arg_rule([renaissance, greet], greeting="Greetings and Salutations")
choice.arg_rule([hip, greet], greeting="Yo")
```

### Combined

The use of choice functions and choice arguments can also be combined:

```python
@choice.func_impl(sort)
@choice.args("reversed")
def insertion_sort(list[int], reversed=False) -> list[int]:
    # Definition here

choice.rule([baz, sort], insertion_sort, reversed=True)
```

## Status

The current status of PyChoice is a work in progress that I am publishing as a demonstration to GitHub. It is not currently being published to PyPi but open an issue if anyone finds this and is interested in it and I can begin doing so. There are also some helper features likely missing from the library such as supporting contexts with a `with` statement, using classes and inheritance, and helpers for patterns of choices like event listeners.

Likewise, the dev tooling is a key component of working with this kind of complexity. For example, understanding which choices are made would be improved with a UI display of the logic. You can debug a function to follow choices, but it would help to have this as a tracing capability. The trace could also then be used for golden testing choices to ensure no changes are made accidentally. It would also help to have integration into documentation tools like sphinx to better expose what choice options are available.

-------

## Resources for after deploying to pypi

- **Documentation** <https://zachgk.github.io/PyChoice/>

[![Release](https://img.shields.io/github/v/release/zachgk/PyChoice)](https://img.shields.io/github/v/release/zachgk/PyChoice)
[![Build status](https://img.shields.io/github/actions/workflow/status/zachgk/PyChoice/main.yml?branch=main)](https://github.com/zachgk/PyChoice/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/zachgk/PyChoice/branch/main/graph/badge.svg)](https://codecov.io/gh/zachgk/PyChoice)
[![Commit activity](https://img.shields.io/github/commit-activity/m/zachgk/PyChoice)](https://img.shields.io/github/commit-activity/m/zachgk/PyChoice)
[![License](https://img.shields.io/github/license/zachgk/PyChoice)](https://img.shields.io/github/license/zachgk/PyChoice)


Repository initiated with [fpgmaas/cookiecutter-uv](https://github.com/fpgmaas/cookiecutter-uv).
Docs for using it [here](https://fpgmaas.github.io/cookiecutter-uv/)
