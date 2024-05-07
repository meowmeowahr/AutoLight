import sys
from enum import Enum
from enum import auto as enum_auto

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

class DisplayStatusTypes(Enum):
    INFO = enum_auto()
    SUCCESS = enum_auto()
    FAILURE = enum_auto()
    END = enum_auto()
    LAUNCH = enum_auto()
    ALL = enum_auto()

DEFAULT_ICON_MAP = {
    DisplayStatusTypes.LAUNCH: "★",
    DisplayStatusTypes.SUCCESS: "✓",
    DisplayStatusTypes.FAILURE: "🗙",
    DisplayStatusTypes.END: "🛑",
    DisplayStatusTypes.INFO: "❖"
}

DEFAULT_COLOR_MAP = {
    DisplayStatusTypes.LAUNCH: "\033[1;32m",
    DisplayStatusTypes.SUCCESS: "\033[32m",
    DisplayStatusTypes.FAILURE: "\033[31m",
    DisplayStatusTypes.END: "\033[35m"
}

class FancyDisplay:
    def __init__(self, display_types: list[DisplayStatusTypes] = [DisplayStatusTypes.ALL], icon_map: dict = DEFAULT_ICON_MAP, color_map: dict = DEFAULT_COLOR_MAP):
        self.display_types = display_types
        self.icon_map = icon_map
        self.color_map = color_map

    def display(self, level: DisplayStatusTypes, text: str):
        if not (level in self.display_types or DisplayStatusTypes.ALL in self.display_types):
            return
        
        if level in self.icon_map:
            icon = self.icon_map[level]
        else:
            icon = f"[{level.name.upper()}]"

        if level in self.color_map:
            color_start = self.color_map[level]
        else:
            color_start = ""

        print(f"{color_start}{icon} - {text}\033[0m")
    