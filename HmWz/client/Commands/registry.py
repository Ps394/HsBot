REGISTRY = []

def register(obj):
    REGISTRY.append(obj)
    return obj