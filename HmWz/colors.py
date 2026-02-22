"""
Das Modul "colors" enthält die Definition der Farben, die im Bot verwendet werden. Es verwendet eine Enum-Klasse, um die verschiedenen Farben zu definieren, die für verschiedene Aktionen und Statusanzeigen im Bot verwendet werden können. Die Farben sind als ANSI-Escape-Sequenzen definiert und können in den Nachrichten des Bots verwendet werden, um visuelle Hervorhebungen zu geben.
"""
from enum import Enum

class Colors(Enum):
    """
    Diese Enum-Klasse definiert die Farben, die im Bot verwendet werden. Jede Farbe ist als ANSI-Escape-Sequenz definiert und kann in den Nachrichten des Bots verwendet werden, um visuelle Hervorhebungen zu geben.
    """

    # Standardfarben
    DEFAULT = "\033[0m"
    DEFAULT_BOLD = "\033[1;0m"
    GREY = "\033[30m"
    GREY_BOLD = "\033[1;30m"
    RED = "\033[31m"
    RED_BOLD = "\033[1;31m"
    GREEN = "\033[32m"
    GREEN_BOLD = "\033[1;32m"
    YELLOW = "\033[33m"
    YELLOW_BOLD = "\033[1;33m"
    BLUE = "\033[34m"
    BLUE_BOLD = "\033[1;34m"
    MAGENTA = "\033[35m"
    MAGENTA_BOLD = "\033[1;35m"
    CYAN = "\033[36m"
    CYAN_BOLD = "\033[1;36m"
    WHITE = "\033[37m"
    WHITE_BOLD = "\033[1;37m"
    SILVER = "\033[90m"
    SILVER_BOLD = "\033[1;90m"

    # Standardfarben Hell
    BRIGHT_RED = "\033[91m"
    BRIGHT_RED_BOLD = "\033[1;91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_GREEN_BOLD = "\033[1;92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_YELLOW_BOLD = "\033[1;93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_BLUE_BOLD = "\033[1;94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_MAGENTA_BOLD = "\033[1;95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_CYAN_BOLD = "\033[1;96m"
    BRIGHT_WHITE = "\033[97m"
    BRIGHT_WHITE_BOLD = "\033[1;97m"