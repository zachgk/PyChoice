# PyChoice

A library for manging choices, options, and configurations across abstraction hierarchy
- **Github repository**: <https://github.com/zachgk/PyChoice/>

The pychoice library is a python implementation of choice as described in this [blog post](https://blog.zachkimberg.com/programming%20languages/doing-things-well/) by Zach Kimberg (who also authored this library). The best way to think of pychoice is that it is a pseudo-new feature of the python programming language implemented as a library. It can be used for how to manage complexity around making modules heavily customizable. And this is done by customizing it through the use of choice. This includes customization across abstraction boundaries. Read the original blog post to understand the deeper philosphy behind the language and why it is designed as it is, but this isn't required as the usage is clear enough from examples.

## Library

Let's say we have a simple greeting function that we will define as a choice function:

```python
@choice.func(args=["greeting"])
def greet(name: str, greeting="Hello"):
    return f"{greeting} {name}"
```

Now we might integrate this function into a larger application like an email broadcast to all subscribers. For example, we might have a call stack like `my_application() > ... > emailBroadCast() > writeEmail() > writeEmailBody() > greet()` where this greeting function is buried in a lot of other functions.

But that means if you want to customize the greeting for your email broadcast, you would have two options. Either every single function in the chain would have to pass on a override greeting which makes them unreadable. Or you would define a dict or class to store an `EmailConfig` which contains the greeting. This works better, but rarely do these configs offer enough flexibility to work for all use cases.

With a choice function, these can be controlled by using choice rules like this:

```python
# Create a choice rule to override the behavior
choice.rule([my_application, greet], greet, greeting="Hi")

# Create another overriding rule
choice.rule([my_application, serious_message, greet], greet, greeting="Dear Sir or Madam")
```

Like this, you can add a collection of rules to determine which greeting you use. And these rules can control functions ignoring abstractinon boundries which should not apply to choices. This includes in other functions, modules, or libraries which can now systematically offer more control by using choice functions.

The rules help define situations where you want to use a particular choice. Some may be broad rules that affect may cases or others can be narrow and targeted to a specific usage. In the case that multiple conflicting rules affect the same situation, the most precise rule takes precedence.

But let's say that the arguments which you (optionally) add to your choice function don't provide enough flexibility. Maybe you need a new format for the greeting. For this, you can define a full override.

Think of the original signature like a function interface. Then you can have multiple implementations of the interface and use choice rules to control which implementation gets used. It would look like:

```python
@choice.func(implements=greet, args=["greeting", "title"])
def greet_with_title(name: str, greeting="Hello", title="user"):
    return f"{greeting} {name} the {title}"

choice.rule([my_application, happy_message, greet], greet_with_title, greeting="Hi", title="best user of my application in the whole wide world")
```

Like this, the choice customization can behave like a systematic code injection system. Remember that it can also inject code into libraries, so it can act as a way for libraries to allow hooks or overrides.

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
