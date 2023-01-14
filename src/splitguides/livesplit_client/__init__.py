from prefab_classes.compiled import prefab_compiler

with prefab_compiler():
    from .messaging import LivesplitMessaging
    from .networking import LivesplitConnection


def get_client(server="localhost", port=16834, timeout=1):
    return LivesplitMessaging(LivesplitConnection(server, port, timeout))
