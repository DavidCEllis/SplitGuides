# ==============================================================================
# Copyright (c) 2022 David C Ellis
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================
#
# Elements of this are taken from David Beazley's Cluegen
#
# David Beazley's Copyright from Cluegen
# ----------------------------------------------------------------------
# Classes generated from type clues.
#
#     https://github.com/dabeaz/cluegen
#
# Author: David Beazley (@dabeaz).
#         http://www.dabeaz.com
#
# Copyright (C) 2018-2021.
#
# Permission is granted to use, copy, and modify this code in any
# manner as long as this copyright message and disclaimer remain in
# the source code.  There is no warranty.  Try to use the code for the
# greater good.
# ----------------------------------------------------------------------
"""
Handle boilerplate generation for classes.

Replaces attrs.

My main use of this is for defining settings objects and attrs
seems rather heavyweight for that.

Based on ideas (and some code) from Cluegen by David Beazley https://github.com/dabeaz/cluegen
"""
__version__ = "v0.4.0"


# EXCEPTIONS #
class PrefabError(Exception):
    pass


class NotPrefabClassError(PrefabError, AttributeError):
    pass


# Need a special object to provide the NOTHING feature while not matching None
# This shouldn't be used in any situation other than to compare with an is statement
# So it doesn't need any complicated properties.
_NOTHING = object()


class DefaultValue:
    """
    Dummy class for default values.
    This avoids the actual default value being interpreted when exec is called.
    """
    def __init__(self, value=None):
        """
        Dummy init function, note that the value is never used or even stored.
        """
        pass


def autogen(func):
    """
    Basically the cluegen function from David Beazley's cluegen
    Modified slightly due to other changes.

    Using this as a decorator indicates that the function will return a string
    which should be used to replace the function itself for that specific class.
    """
    def __get__(self, instance, cls):
        # We might need locals if there are some default values that use classes
        # However these won't be the locals from this module but those where
        # the class is defined
        global_vars = {"DefaultValue": DefaultValue}
        local_vars = {}
        code = func(cls)
        exec(code, global_vars, local_vars)
        # Having executed the code, the method should now exist
        # and can be retrieved by name from the dict
        method = local_vars[func.__name__]
        # Replace the attribute with the real function - this will only be called once.
        setattr(cls, func.__name__, method)
        return method.__get__(instance, cls)

    def __set_name__(self, cls, name):
        # Add this method to the _methods list to be generated with the subclass
        cls._methods.append((name, self))

    return type(f'AutoGen_{func.__name__}', (), dict(__get__=__get__, __set_name__=__set_name__))()


class Attribute:
    """
    Descriptor class to define attributes.

    This replaces the use of type hints in cluegen.
    """
    # noinspection PyProtectedMember
    def __set_name__(self, owner, name):
        # Here we append any generated attributes to a private variable
        # This will be used instead of cluegen's all_clues.
        if not issubclass(owner, Prefab):
            raise NotPrefabClassError(
                "Attempted to use Attribute outside of a Prefab derived class."
            )

        # Make a new list for this class if it doesn't exist.
        # The class name is used to avoid sharing a list with a parent class.
        attribute_var = f'_{owner.__name__}_attributes'
        sub_attributes = getattr(owner, attribute_var, {})
        sub_attributes[name] = self
        setattr(owner, attribute_var, sub_attributes)

        self.private_name = f'_{name}'

    def __get__(self, obj, objtype=None):
        if self.default is _NOTHING:
            return getattr(obj, self.private_name)
        return getattr(obj, self.private_name, self.default)

    def __set__(self, obj, value):
        # Detect if the value is a default placeholder and replace
        # it with the real value.
        if isinstance(value, DefaultValue):
            value = self.default
        if self.converter:
            value = self.converter(value)
        setattr(obj, self.private_name, value)

    # noinspection PyShadowingBuiltins
    def __init__(self, *, default=_NOTHING, converter=None, init=True, repr=True):
        """
        Create an Attribute for a prefab
        :param default: Default value for this attribute
        :param converter: prefab.attr = x -> prefab.attr = converter(x)
        :param init: Include this attribute in the __init__ parameters
        :param repr: Include this attribute in the class __repr__
        """
        if not init and default is _NOTHING:
            raise PrefabError("Must provide a default value if the attribute is not in init.")
        self.default = default
        self.converter = converter
        self.init = init
        self.repr = repr


# noinspection PyReturnFromInit,PyMethodParameters
class Prefab:
    """
    The main prefab class - The one to inherit from.
    """
    _attributes = {}
    _methods = []

    def __init_subclass__(cls):
        super().__init_subclass__()
        # Make sure the original methods are regenerated for each subclass.
        # Without this they will inherit directly from the parent and when
        # the parent's method is used it will be resolved for the parent's
        # attributes.
        for name, val in cls._methods:
            setattr(cls, name, val)

        # Get all attributes
        attributes = {name: attrib for c in reversed(cls.__mro__)
                      for name, attrib in getattr(c, f'_{c.__name__}_attributes', {}).items()}
        if not attributes:
            # It's easier to throw an error than to rewrite
            # The code for the useless case of a class with no attributes.
            # Note - this will show up as a runtime error with this as the cause.
            raise PrefabError("Class must contain at least 1 attribute.")
        cls._attributes = attributes
        cls.__match_args__ = tuple(name for name in cls._attributes)

    @autogen
    def __init__(cls):
        arglist = []
        for name, attrib in cls._attributes.items():
            if attrib.init:
                if hasattr(cls, name):
                    attr_value = getattr(cls, name)
                    if isinstance(attr_value, (str, int, float, bool)):
                        arg = f'{name}={getattr(cls, name)!r}'
                    else:
                        arg = f'{name}=DefaultValue("{name}")'
                else:
                    arg = name
                arglist.append(arg)
        args = ', '.join(arglist)

        assignments = (
            (name, name) if attrib.init else (name, f'DefaultValue("{name}")')
            for name, attrib in cls._attributes.items()
        )
        body = '\n'.join(
            f"    self.{name} = {value}"
            for name, value in assignments
        )

        code = f"def __init__(self, {args}):\n{body}\n"
        return code

    @autogen
    def __repr__(cls):
        content = ', '.join(
            f"{name}={{self.{name}!r}}"
            for name, attrib in cls._attributes.items()
            if attrib.repr
        )
        code = f"def __repr__(self):\n    return f'{{type(self).__name__}}({content})'"
        return code

    @autogen
    def __iter__(cls):
        values = '\n'.join(f'    yield self.{name} ' for name in cls._attributes.keys())
        code = f"def __iter__(self):\n{values}"
        return code

    @autogen
    def __eq__(cls):
        selfvals = ','.join(f'self.{name}' for name in cls._attributes.keys())
        othervals = ','.join(f'other.{name}' for name in cls._attributes.keys())
        class_comparison = "self.__class__ is other.__class__"
        instance_comparison = f"({selfvals},) == ({othervals},)"
        code = (
            f"def __eq__(self, other):\n"
            f"    return {instance_comparison} if {class_comparison} else NotImplemented\n"
        )
        return code

    # Additional motivating methods
    def to_dict(self):
        return {name: getattr(self, name) for name in self._attributes.keys()}

    def to_json(self, *, excludes=None, indent=2, default=str, **kwargs):
        """
        Output the class attributes as JSON
        :param excludes:
        :param indent: indent for json
        :param default: default converter for json
        :return:
        """
        # This should only be imported if this method is called
        import json

        if excludes:
            out_dict = {
                key: value
                for key, value in self.to_dict().items()
                if key not in excludes
            }
        else:
            out_dict = self.to_dict()

        return json.dumps(out_dict, indent=indent, default=default, **kwargs)
