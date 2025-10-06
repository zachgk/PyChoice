# Functions

This guide covers the fundamental building blocks of PyChoice: creating choice (interface) functions and implementations.

## Creating Choice Functions

Choice functions are the core concept in PyChoice. They allow you to define functions that can have their behavior customized through rules and overloaded with various implementations.

### Basic Choice Function

Use the `@choice.func()` decorator to create a choice function:

```python
import pychoice as choice

@choice.func()
def greet(name: str):
    return f"Hello {name}"

# Basic usage
print(greet("World"))  # Output: Hello World
```

### Choice Arguments

Choice functions become powerful when you define choice arguments using the `args` parameter:

```python
@choice.func(args=["greeting"])
def greet(name: str, greeting="Hello"):
    return f"{greeting} {name}"

# The greeting parameter can now be customized via rules
print(greet("World"))  # Output: Hello World
```

### Email System Example

Let's build a practical example using an email system that needs different greeting styles:

```python
@choice.func(args=["greeting"])
def greet(name: str, greeting="Hello"):
    return f"{greeting} {name}"

def my_application():
    return email_broadcast()

def email_broadcast():
    return write_email()

def write_email():
    return write_email_body()

def write_email_body():
    # Greeting is called deep in the call stack
    message = greet("John")
    return f"Email body: {message}"

# Run the application
result = my_application()
print(result)  # Output: Email body: Hello John
```

## Choice Implementations

You can create entirely different implementations of a choice function using `@choice.impl`:

### Creating Additional Implementations

```python
@choice.impl(implements=greet)
def formal_greet(name: str):
    return f"Dear {name}"

@choice.impl(implements=greet, args=["greeting", "title"])
def greet_with_title(name: str, greeting="Hello", title="user"):
    return f"{greeting} {name} the {title}"
```

### Wrapping Functions

You can also wrap existing functions to make them choice-compatible:

```python
def simple_greet(name: str):
    return f"Hi {name}"

# Wrap an existing function
wrapped_greet = choice.wrap(simple_greet, implements=greet)
```

## Function Testing and Debugging

### Basic Testing

Test your choice functions like regular Python functions:

```python
def test_basic_greeting():
    assert greet("test") == "Hello test"

def test_custom_greeting():
    # This will use a rule (covered in Rules documentation)
    assert greet("test") == "Hi test"
```

### Tracing Function Calls

PyChoice includes tracing capabilities to help understand function behavior:

```python
# Start tracing
choice.trace_start()

# Run your functions
result = my_application()

# Stop tracing and examine results
trace = choice.trace_stop()
print(trace)  # Shows which choice functions were called

# Save trace for analysis
trace.save("function_trace.json")
```

## Choice Arguments

Choice function implementations (both default and additional implementations) can have choice arguments. These allow you to parameterize the implementation so there are additional dimensions they can be later customized through rules.

```python
@choice.func(args=["format", "prefix"])
def format_message(content: str, format="text", prefix=""):
    """
    content: regular parameter (required)
    format: choice argument with default
    prefix: choice argument with default
    """
    message = f"{prefix}{content}" if prefix else content

    if format == "text":
        return message
    elif format == "html":
        return f"<p>{message}</p>"
    elif format == "markdown":
        return f"**{message}**"

    return message
```
