"""Command line formatting, prompts, and other utilities."""

import re
from blessings import Terminal

# Globals

_term = Terminal()

# Keys into COLORS
ERROR = 'error'
ERROR_TITLE = 'error_title'
WARNING = 'warning'
SUCCESS = 'success'
INFO = 'info'
PROMPT = 'prompt'
#: Dictionary mapping indices to formatting functions
COLORS = {
    None: str,
    ERROR: _term.red,
    ERROR_TITLE: _term.bold_red,
    WARNING: _term.yellow,
    SUCCESS: _term.green,
    INFO: _term.cyan,
    PROMPT: _term.magenta,
}
#: String to use when indenting output
INDENT = ' ' * 4


# Output Formatting

def print_multiline(first_line, *lines,
                    formatting=None, first_line_formatting=None,
                    indent=True, indent_first_line=False):
    """Print multiple lines

    :param first_line: First line to print
    :param lines: Positional parameters will each be printed on their own line
    :param formatting: (Optional) Set to a formatting constant to format each
        line
    :param first_line_formatting: (Optional) Set to override formatting for the
        first line
    :param indent: (Default: True) If True and there's multiple lines, indent
        all lines after the first
    :param indent_first_line: (Default: False) If True, indent the first line
    """
    if formatting not in COLORS:
        formatting = None
    if first_line_formatting is None or first_line_formatting not in COLORS:
        first_line_formatting = formatting
    fmt_func = COLORS[formatting]
    first_line_fmt_func = COLORS[first_line_formatting]

    first_line_prefix = INDENT if indent_first_line else ''
    print(first_line_fmt_func(first_line_prefix + str(first_line)))

    if lines:
        line_prefix = INDENT if indent else ''
        for line in lines:
            print(fmt_func(line_prefix + str(line)))


def print_error(*lines):
    print_multiline(*lines, first_line_formatting=ERROR_TITLE, formatting=ERROR)


def print_warning(*lines):
    print_multiline(*lines, formatting=WARNING)


def print_success(*lines):
    print_multiline(*lines, formatting=SUCCESS)


def print_info(*lines):
    print_multiline(*lines, formatting=INFO)


# User Input Prompts

def sanitize_input(val):
    return val.strip()


class ValidationError(Exception):
    """Raised if input validation fails"""
    pass


def validate_optional_prompt(val, error_msg=None):
    """Dummy validation function for optional prompts. Just returns val"""
    # TODO Should there just be an option in prompt()? If input is non-blank you'll probably still wanna validate it
    return val


def validate_nonempty(val, error_msg=None):
    """Raises ValidationError if val is empty

    :param val: Input to validate
    :param error_msg: (Optional) Custom error text to print if val is invalid

    :return: Validated input
    """
    if not val:
        raise ValidationError(error_msg or 'Please enter some text.')
    return val


def validate_yn(val, error_msg=None):
    """Validate y/n prompts

    :param val: User response to y/n prompt. If a boolean value is passed
        (e.g. if a prompt received initial_input=True), it is treated as a y/n
        answer and considered valid input
    :param error_msg: (Optional) Custom error text to print if val is invalid

    :return: True if user answered yes, False if user answered no
    """
    # If a boolean value was passed, return it
    if isinstance(val, bool):
        return val
    val = val.lower().strip()
    if val not in ['y', 'yes', 'n', 'no']:
        raise ValidationError(error_msg or 'Please enter "y" or "n".')
    return val in ['y', 'yes']


def generate_validate_regex_function(expr, default_error_msg='No matches found.', show_expr_in_error_msg=True):
    """Generate a validation function that validates a given regular expression.

    :param expr: Regular expression to validate against
    :param default_error_msg: (Optional) Default validation error message to use
        in this validation function
    :param show_expr_in_error_msg: (Default: True) If True, expr will be shown
        in error message

    :return: Generated validation function
    """
    def validate_regex(val, error_msg=None):
        if not error_msg:
            error_msg = default_error_msg
        if show_expr_in_error_msg:
            error_msg += '\n' + INDENT + 'Must match regex: ' + expr
        res = re.findall(expr, val)
        if not res:
            raise ValidationError(error_msg)
        return res[0]
    return validate_regex


def prompt(prompt_text, *extended_description,
           initial_input=None, default_val=None,
           sanitize_function=sanitize_input, validate_function=validate_nonempty, format_function=None,
           invalid_msg=None, print_newline_on_success=True):
    """Prompt user for input

    :param prompt_text: Text to display next to input area
    :param *extended_description: (Optional) Explanation of prompt. Printed
        before prompt. Each positional parameter here is printed on its own
        line

    :param initial_input: (Optional) Initial input (e.g. something passed in
        via command line args). If it passes validation, will use this and skip
        the input prompt
    :param default_val: (Optional) Value to use if no input is provided

    :param sanitize_function: (Default: sanitize_input) Function to sanitize
        input
    :param validate_function: (Default: validate_nonempty) Function used to
        validate input
    :param format_function: (Optional) Function to format input after running
        it through sanitize_function and before passing it to validate_function

    :param invalid_msg: (Optional) Error message text to display if validation
        fails
    :param print_newline_on_success: (Default: True) Print a newline after
        successfully getting valid input

    :return: Input after sanitization, formatting, and validation
    """
    # If input for this prompt was given via an argument, attempt to validate
    # it and bypass prompt
    if initial_input is not None:
        try:
            initial_input = sanitize_function(initial_input)
            if format_function is not None:
                initial_input = format_function(initial_input)
            val = validate_function(initial_input, invalid_msg)
        except ValidationError as e:
            print_error(e)
        else:
            return val
    # Print description and prompt
    if extended_description:
        print(*extended_description, sep='\n')
    text = COLORS[PROMPT]('> ' + (
        f'{prompt_text} [{default_val}]'
        if default_val is not None else
        prompt_text
    ) + ': ')
    # Loop until we get valid input
    while True:
        val = sanitize_function(input(text))
        # If we have a default val, use it if input is empty
        if not val and default_val is not None:
            val = default_val
        # Format val
        if format_function is not None:
            val = format_function(val)
        # Attempt to validate, loop if invalid
        try:
            val = validate_function(val, invalid_msg)
        except ValidationError as e:
            print_error(e)
            continue
        break
    if print_newline_on_success:
        print('')
    return val

