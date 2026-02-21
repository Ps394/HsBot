from dataclasses import dataclass
from enum import Enum

"""
Das Modul "colors" enthält die Definition der Farben, die im Bot verwendet werden. Es verwendet eine Enum-Klasse, um die verschiedenen Farben zu definieren, die für verschiedene Aktionen und Statusanzeigen im Bot verwendet werden können. Die Farben sind als ANSI-Escape-Sequenzen definiert und können in den Nachrichten des Bots verwendet werden, um visuelle Hervorhebungen zu geben.
"""

@dataclass(frozen=True)
class Colors(Enum):
    """
    Diese Enum-Klasse definiert die Farben, die im Bot verwendet werden. Jede Farbe ist als ANSI-Escape-Sequenz definiert und kann in den Nachrichten des Bots verwendet werden, um visuelle Hervorhebungen zu geben.
    """

    # Standardfarben
    default = "\033[0m"
    default_bold = "\033[1;0m"
    grey = "\033[30m"
    grey_bold = "\033[1;30m"
    red = "\033[31m"
    red_bold = "\033[1;31m"
    green = "\033[32m"
    green_bold = "\033[1;32m"
    yellow = "\033[33m"
    yellow_bold = "\033[1;33m"
    blue = "\033[34m"
    blue_bold = "\033[1;34m"
    magenta = "\033[35m"
    magenta_bold = "\033[1;35m"
    cyan = "\033[36m"
    cyan_bold = "\033[1;36m"
    white = "\033[37m"
    white_bold = "\033[1;37m"
    silver = "\033[90m"
    silver_bold = "\033[1;90m"

    # Standardfarben Hell
    bright_red = "\033[91m"
    bright_red_bold = "\033[1;91m"
    bright_green = "\033[92m"
    bright_green_bold = "\033[1;92m"
    bright_yellow = "\033[93m"
    bright_yellow_bold = "\033[1;93m"
    bright_blue = "\033[94m"
    bright_blue_bold = "\033[1;94m"
    bright_magenta = "\033[95m"
    bright_magenta_bold = "\033[1;95m"
    bright_cyan = "\033[96m"
    bright_cyan_bold = "\033[1;96m"
    bright_white = "\033[97m"
    bright_white_bold = "\033[1;97m"