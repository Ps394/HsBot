"""
Das Modul "emojis" enthält die Definition der Emojis, die im Bot verwendet werden. Es verwendet eine Enum-Klasse, um die verschiedenen Emojis zu definieren, die für verschiedene Aktionen und Statusanzeigen im Bot verwendet werden können. Die Emojis sind als Unicode-Zeichen definiert und können in den Nachrichten des Bots verwendet werden, um visuelle Hinweise zu geben.
"""
from enum import Enum

class Emojis(Enum):
     """
     Diese Enum-Klasse definiert die Emojis, die im Bot verwendet werden. Jedes Emoji ist als Unicode-Zeichen definiert und kann in den Nachrichten des Bots verwendet werden, um visuelle Hinweise zu geben.
     """
     SUCCESS = "✅"
     WARNING = "⚠️"
     ERROR = "⛔"

     REGISTER = "✅"
     REREGISTER = "🔄"
     UNREGISTER = "❌"

     TOTAL_REGISTRATIONS = "📊"
     PERMA_REGISTRATION = "🔒"
     NORMAL_REGISTRATION = "🔓"
