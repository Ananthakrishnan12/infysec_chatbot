from bson import ObjectId


def serialize_doc(obj):
    """Recursively convert MongoDB ObjectIds to string."""

    if isinstance(obj, list):
        return [serialize_doc(item) for item in obj]

    if isinstance(obj, dict):
        new_doc = {}
        for key, value in obj.items():
            new_doc[key] = serialize_doc(value)
        return new_doc

    if isinstance(obj, ObjectId):
        return str(obj)

    return obj
