# Tutorial

This tutorial provides detailed examples of using PyChoice to manage complexity in your applications.

## Email System Example

Let's build a comprehensive example using an email system that needs different greeting styles based on context.

### Basic Setup

First, let's create our core choice function:

```python
import pychoice as choice

@choice.func(args=["greeting"])
def greet(name: str, greeting="Hello"):
    return f"{greeting} {name}"
```

### Application Context

Now let's create the application structure:

```python
def my_application():
    email_broadcast()

def email_broadcast():
    write_email()

def write_email():
    write_email_body()

def write_email_body():
    # This is where the greeting gets called, deep in the call stack
    message = greet("John")
    return f"Email body: {message}"
```

### Adding Rules

We can now add rules to customize the greeting based on different contexts:

```python
# Basic customization for the application
choice.rule([my_application, greet], greet, greeting="Hi")

# More specific rule for serious messages
def serious_message():
    return write_email_body()

choice.rule([my_application, serious_message, greet], greet, greeting="Dear Sir or Madam")
```

### Testing the Rules

```python
# Run the application
result = my_application()
print(result)  # Uses "Hi John" greeting

# Test serious message context
result = serious_message()  
print(result)  # Uses "Dear Sir or Madam John" greeting
```

## Advanced: Alternative Implementations

For more complex customization, we can create entirely new implementations:

### Creating Alternative Implementation

```python
@choice.impl(implements=greet, args=["greeting", "title"])
def greet_with_title(name: str, greeting="Hello", title="user"):
    return f"{greeting} {name} the {title}"
```

### Using Alternative Implementation

```python
def happy_message():
    return write_email_body()

# Use the title implementation for happy messages
choice.rule([my_application, happy_message, greet], greet_with_title, 
           greeting="Hi", title="best user of my application in the whole wide world")
```

## Rule Precedence

PyChoice uses rule specificity to determine precedence. More specific rules take precedence over general ones:

```python
# General rule (applies broadly)
choice.rule([my_application, greet], greet, greeting="Hi")

# More specific rule (takes precedence)
choice.rule([my_application, email_broadcast, greet], greet, greeting="Hey")

# Most specific rule (highest precedence)
choice.rule([my_application, email_broadcast, write_email, greet], greet, greeting="Hello there")
```

## Working with Classes

PyChoice can also work with class methods:

```python
class EmailService:
    @choice.func(args=["format"])
    def format_message(self, content: str, format="text"):
        if format == "text":
            return content
        elif format == "html":
            return f"<p>{content}</p>"
        return content

# Rule for HTML formatting in web context
def web_context():
    service = EmailService()
    return service.format_message("Hello World")

choice.rule([web_context, EmailService.format_message], 
           EmailService.format_message, format="html")
```

## Tracing and Debugging

PyChoice includes tracing capabilities to help understand which choices are made:

```python
# Start tracing
choice.trace_start()

# Run your application
my_application()

# Stop tracing and get results
trace = choice.trace_stop()
print(trace)  # Shows the choice decisions made

# Save trace to file for analysis
trace.save("trace.json")
```

## Context Management

You can use context managers for temporary rule overrides:

```python
class DebugContext(choice.ChoiceContext):
    pass

@choice.func(args=["level"])
def log(message: str, level="INFO"):
    print(f"[{level}] {message}")

# Rule that applies only within DebugContext
choice.rule([DebugContext, log], log, level="DEBUG")

# Usage
with DebugContext():
    log("This is a debug message")  # Prints: [DEBUG] This is a debug message

log("This is outside context")  # Prints: [INFO] This is outside context
```

## Next Steps

- Explore the [API Reference](modules.md) for detailed function documentation
- Learn about visualization features for understanding rule complexity
- Check out the source code examples in the test files
