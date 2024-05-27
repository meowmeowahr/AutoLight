import sys


def banner(only_intercative=True):
    text = """
    \033[36m
     █████╗ ██╗   ██╗████████╗ ██████╗       ██╗     ██╗ ██████╗ ██╗  ██╗████████╗
    ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗      ██║     ██║██╔════╝ ██║  ██║╚══██╔══╝
    ███████║██║   ██║   ██║   ██║   ██║█████╗██║     ██║██║  ███╗███████║   ██║   
    ██╔══██║██║   ██║   ██║   ██║   ██║╚════╝██║     ██║██║   ██║██╔══██║   ██║   
    ██║  ██║╚██████╔╝   ██║   ╚██████╔╝      ███████╗██║╚██████╔╝██║  ██║   ██║   
    ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝       ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝\033[0m
    """
    if (only_intercative and is_interactive()) or not only_intercative:
        print(text)


def is_interactive():
    return sys.stdout.isatty()

def ask_yes_no(question: str, default='y'):
    if default not in ['y', 'n']:
        raise ValueError("Default must be 'y' or 'n'.")

    default_prompt = " [Y/n] " if default == 'y' else " [y/N] "

    user_input = input(question + default_prompt).strip().lower()

    if user_input == '':
        user_input = default
    
    if user_input in ['y', 'n']:
        return user_input == 'y'
    else:
        return default
