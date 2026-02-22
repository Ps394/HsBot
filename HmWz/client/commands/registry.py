REGISTRY = []

def register(obj):
    """
    Registriert einen Command oder eine CommandGroup in der globalen Registry.
    Verhindert doppelte Einträge.
    
    :param obj: Das zu registrierende Objekt (Command oder Group)
    :return: Das registrierte Objekt
    """
    if obj not in REGISTRY:
        REGISTRY.append(obj)
    return obj