"""
Dieses Modul enthält die Definition der Registry und den Dekorator zum Registrieren von Übersichten, die in diesem Bot verwendet werden.

:mod:`REGISTRY` ist eine Liste von Übersichtsklassen, die mit dem Dekorator :func:`register` registriert wurden. 

Der Dekorator :func:`register` fügt die dekorierte Übersichtsklasse zur REGISTRY hinzu, wenn sie noch nicht vorhanden ist, und gibt die Klasse zurück. Dadurch können Übersichtsklassen einfach registriert und verwaltet werden, ohne dass manuelle Änderungen an der REGISTRY erforderlich sind.
"""
from typing import List
from .basic_overview import BasicOverviewType

REGISTRY: List[BasicOverviewType] = []
"""Registry für alle Übersichten, die in diesem Bot verwendet werden."""

def register(cls: BasicOverviewType) -> BasicOverviewType:
    """Dekorator zum Registrieren einer Übersichtsklasse im REGISTRY.

    :param cls: Die Übersichtsklasse, die registriert werden soll.
    :type cls: BasicOverviewType
    :return: Die registrierte Übersichtsklasse.
    :rtype: BasicOverviewType
    """
    if cls not in REGISTRY:
        REGISTRY.append(cls)
    return cls