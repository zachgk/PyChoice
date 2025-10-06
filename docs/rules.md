# Rules

This guide covers PyChoice's powerful rule system for customizing function behavior. Rules allow you to modify how choice functions behave in different contexts without changing the original function code.

## Basic Rules

### Simple Rule Creation

Use `choice.rule()` to customize choice function behavior:

```python
import pychoice as choice

@choice.func(args=["greeting"])
def greet(name: str, greeting="Hello"):
    return f"{greeting} {name}"

def my_application():
    return greet("World")

# Create a rule that applies when my_application calls greet
choice.rule([my_application, greet], greet, greeting="Hi")

print(my_application())  # Output: Hi World
```

Here, there are several components of a choice rule. The first component is the selector that describes when the rule is applied. The last component of the selector must be a choice function while the first selector components can describe the general situation.

The second argument describes what implementation to use for the choice function. Finally, the keyword arguments can be used to override the choice arguments for the implementation.

### Specifying the Choice Implementation

Rules can specify different implementations to use:

```python
@choice.impl(implements=greet)
def formal_greet(name: str):
    return f"Dear {name}"

def business_context():
    return greet("Client")

# Use the formal implementation in business context
choice.rule([business_context, greet], formal_greet)

print(business_context())  # Output: Dear Client
```


### Argument-Only Rules

You can create rules that only modify arguments without changing the implementation:

```python
def test_custom_greeting():
    return greet("Alice")

# Rule that only provides arguments (None implementation)
choice.rule([test_custom_greeting, greet], None, greeting="Greetings")

print(test_custom_greeting())  # Output: Greetings Alice
```

## Rule Precedence

PyChoice uses rule specificity to determine precedence. More specific rules  take precedence over general ones.

### Understanding Precedence

```python
@choice.func(args=["greeting"])
def greet(name: str, greeting="Hello"):
    return f"{greeting} {name}"

def my_application():
    return email_broadcast()

def email_broadcast():
    return write_email()

def write_email():
    return greet("User")

# General rule (applies broadly)
choice.rule([my_application, greet], greet, greeting="Hi")

# More specific rule (takes precedence)
choice.rule([my_application, email_broadcast, greet], greet, greeting="Hey")

# Most specific rule (highest precedence)
choice.rule([my_application, email_broadcast, write_email, greet], greet, greeting="Hello there")

print(my_application())  # Output: Hello there User
```

## Advanced Rule Forms

### Class-Based Selectors

Rules can target specific class methods using tuple syntax:

```python
@choice.func()
def process_data():
    return "default"

@choice.impl(implements=process_data)
def optimized_process():
    return "optimized"

class DataProcessor:
    def run_analysis(self):
        return process_data()

class FastProcessor(DataProcessor):
    def run_fast_analysis(self):
        return process_data()

# Rule for specific class and method
choice.rule([(DataProcessor, "run_analysis"), process_data], optimized_process)

# Rule for parent class method (affects subclasses too)
choice.rule([(DataProcessor, "run_fast_analysis"), process_data], optimized_process)

# Usage
processor = DataProcessor()
fast_processor = FastProcessor()

print(processor.run_analysis())  # Output: optimized
print(fast_processor.run_fast_analysis())  # Output: optimized
```

### Context Managers

Create scoped rules using context managers:

```python
class DebugContext(choice.ChoiceContext):
    pass

class ProductionContext(choice.ChoiceContext):
    pass

@choice.func(args=["level"])
def log(message: str, level="INFO"):
    return f"[{level}] {message}"

# Rules that apply only within specific contexts
choice.rule([DebugContext, log], log, level="DEBUG")
choice.rule([ProductionContext, log], log, level="WARN")

# Usage
print(log("Normal message"))  # Output: [INFO] Normal message

with DebugContext():
    print(log("Debug message"))  # Output: [DEBUG] Debug message

with ProductionContext():
    print(log("Prod message"))  # Output: [WARN] Prod message
```

## Dynamic Rules

### Rules with Capture Logic

Use `@choice.def_rule` to create dynamic rules that can inspect function calls:

```python
@choice.func(args=["greeting"])
def greet(name: str, greeting="Hello"):
    return f"{greeting} {name}"

def wrap_greet(name: str):
    return greet(name)

def test_dynamic():
    return wrap_greet("Dynamic")

@choice.def_rule([test_dynamic, wrap_greet, greet])
def dynamic_rule(captures):
    """
    The docstring here is used to document the underlying reasons behind the rule
    captures[0]: Arguments to test_dynamic
    captures[1]: Arguments to wrap_greet
    captures[2]: Arguments to greet
    """
    # Access the name parameter from wrap_greet call
    name = captures[1]['name']
    return greet, {"greeting": f"Dynamic {name}"}

print(test_dynamic())  # Output: Dynamic Dynamic Dynamic
```

### Conditional Rules

Rules can return `None` to skip application:

```python
@choice.def_rule([greet])
def conditional_rule(captures):
    """Only apply rule for specific names"""
    if "name" in captures[0] and captures[0]["name"] == "special":
        return greet, {"greeting": "Very Special"}
    return None  # Don't apply rule for other names

print(greet("normal"))   # Output: Hello normal
print(greet("special"))  # Output: Very Special special
```

## Argument Matching

### Pattern Matching Rules

Use `choice.Match` to create rules based on function arguments:

```python
# Rule that applies only when greet is called with name="VIP"
choice.rule([choice.Match(greet, name="VIP")], greet, greeting="Welcome")

print(greet("User"))  # Output: Hello User
print(greet("VIP"))   # Output: Welcome VIP
```

### Complex Matching Logic

Combine matching with dynamic rules:

```python
@choice.def_rule([greet])
def smart_greeting_rule(captures):
    """Apply different greetings based on name patterns"""
    if "name" not in captures[0]:
        return None

    name = captures[0]["name"]

    if name.startswith("Dr."):
        return greet, {"greeting": "Good day"}
    elif name.startswith("Prof."):
        return greet, {"greeting": "Greetings"}
    elif name.isupper():
        return greet, {"greeting": "Hey"}

    return None

print(greet("Dr. Smith"))    # Output: Good day Dr. Smith
print(greet("Prof. Jones"))  # Output: Greetings Prof. Jones
print(greet("ROBOT"))        # Output: Hey ROBOT
print(greet("Alice"))        # Output: Hello Alice
```
