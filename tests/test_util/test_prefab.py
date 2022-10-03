import pytest

from splitguides.util.prefab import Prefab, Attribute, ClassGenError, NotAPrefabError
from pathlib import Path, WindowsPath


def test_basic_subclass():
    class Coordinate(Prefab):
        x = Attribute()
        y = Attribute()

    x = Coordinate(1, 2)

    assert (x.x, x.y) == (1, 2)


def test_basic_with_defaults():
    class Coordinate(Prefab):
        x = Attribute(default=0)
        y = Attribute(default=0)

    x = Coordinate()
    assert (x.x, x.y) == (0, 0)

    y = Coordinate(y=5)
    assert (y.x, y.y) == (0, 5)


def test_basic_composition():
    class Coordinate(Prefab):
        x = Attribute()
        y = Attribute()

    class CoordinateZ(Prefab):
        z = Attribute()

    class Coordinate3D(CoordinateZ, Coordinate):
        pass

    x = Coordinate3D(1, 2, 3)

    assert (x.x, x.y, x.z) == (1, 2, 3)


def test_basic_inheritance():
    class Coordinate(Prefab):
        x = Attribute()
        y = Attribute()

    class Coordinate3D(Coordinate):
        z = Attribute()

    x = Coordinate3D(1, 2, 3)

    assert (x.x, x.y, x.z) == (1, 2, 3)


def test_inheritance_and_composition():
    class Coordinate(Prefab):
        x = Attribute()
        y = Attribute()

    class Coordinate3D(Coordinate):
        z = Attribute()

    class CoordinateTime(Prefab):
        t = Attribute()

    class Coordinate4D(CoordinateTime, Coordinate3D):
        pass

    x = Coordinate4D(1, 2, 3, 4)

    assert (x.x, x.y, x.z, x.t) == (1, 2, 3, 4)


def test_repr():
    class Coordinate(Prefab):
        x = Attribute()
        y = Attribute()

    expected_repr = "Coordinate(x=1, y=2)"

    assert repr(Coordinate(1, 2)) == expected_repr


def test_iter():
    class Coordinate(Prefab):
        x = Attribute()
        y = Attribute()

    x = Coordinate(1, 2)

    y = list(x)
    assert y == [1, 2]


def test_eq():
    class Coordinate(Prefab):
        x = Attribute()
        y = Attribute()

    class Coordinate3D(Coordinate):
        z = Attribute()

    class CoordinateTime(Prefab):
        t = Attribute()

    class Coordinate4D(CoordinateTime, Coordinate3D):
        pass

    x = Coordinate4D(1, 2, 3, 4)
    y = Coordinate4D(1, 2, 3, 4)

    assert (x.x, x.y, x.z, x.t) == (y.x, y.y, y.z, y.t)
    assert x == y


def test_neq():
    class Coordinate(Prefab):
        x = Attribute()
        y = Attribute()

    class Coordinate3D(Coordinate):
        z = Attribute()

    class CoordinateTime(Prefab):
        t = Attribute()

    class Coordinate4D(CoordinateTime, Coordinate3D):
        pass

    x = Coordinate4D(1, 2, 3, 4)
    y = Coordinate4D(5, 6, 7, 8)

    assert (x.x, x.y, x.z, x.t) != (y.x, y.y, y.z, y.t)
    assert x != y


def test_hash():
    class Coordinate(Prefab):
        x = Attribute(default=0)
        y = Attribute(default=0)

    x = Coordinate()
    y = Coordinate(0, 0)

    assert x.__hash__() == y.__hash__() == hash((0, 0))


def test_dict_key():
    class Coordinate(Prefab):
        x = Attribute(default=0)
        y = Attribute(default=0)

    x = Coordinate()
    y = Coordinate(0, 0)
    z = Coordinate(0, 1)

    d = {x: 0}
    assert d[y] == 0

    with pytest.raises(KeyError):
        d[z]


def test_todict():
    class Coordinate(Prefab):
        x = Attribute()
        y = Attribute()

    x = Coordinate(1, 2)

    expected_dict = {'x': 1, 'y': 2}

    assert x.to_dict() == expected_dict


def test_tojson():
    import json
    from pathlib import PurePosixPath  # Not looking to handle windows '\' issues

    class SystemPath(Prefab):
        filename = Attribute()
        path = Attribute(converter=PurePosixPath)

    pth = SystemPath('testfile', 'path/to/test')

    # Check it's a Path internally
    assert pth.path == PurePosixPath('path/to/test')
    assert pth.to_dict()['path'] == PurePosixPath('path/to/test')

    expected_json = json.dumps({'filename': 'testfile', 'path': 'path/to/test'}, indent=2)
    assert pth.to_json() == expected_json

    expected_json = json.dumps({'path': 'path/to/test'}, indent=2)
    assert pth.to_json(excludes=['filename']) == expected_json


def test_converter():
    from pathlib import Path

    class SystemPath(Prefab):
        path = Attribute(converter=Path)

    pth = SystemPath('fake/directory')

    assert pth.path == Path('fake/directory')


def test_default_converter():
    from pathlib import Path

    class SystemPath(Prefab):
        path = Attribute(default='fake/directory', converter=Path)

    pth = SystemPath()

    assert pth.path == Path('fake/directory')


def test_no_default():
    class Coordinate(Prefab):
        x = Attribute()
        y = Attribute()

    with pytest.raises(TypeError):
        x = Coordinate(1)


def test_dumb_error():
    with pytest.raises(ClassGenError):
        class Empty(Prefab):
            pass


def test_not_prefab():
    with pytest.raises(RuntimeError) as e:
        class Rebuild:
            x = Attribute()

    assert isinstance(e.value.__cause__, NotAPrefabError)


def test_difficult_defaults():

    class Settings(Prefab):
        """
        Global persistent settings handler
        """
        _globals = globals()
        output_file = Attribute(default=Path("Settings.json"))

    x = Settings()

    assert x.output_file == Path("Settings.json")
