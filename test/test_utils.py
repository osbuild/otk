from otk.utils import HiddenAttrDict, HiddenAttrList


def test_hidden_attr():
    # Attribute Access
    obj = HiddenAttrDict(a="some_value", sub={"x": "sub_value"})
    assert obj.a == "some_value"
    assert obj.sub.x == "sub_value"

    # Hidden Attribute Access
    obj.set_attribute("a", "src", "hidden_source_for_a")
    obj.sub.set_attribute("x", "src", "hidden_source_for_x")

    assert obj.get_attribute("a", "src") == "hidden_source_for_a"
    assert obj.sub.get_attribute("x", "src") == "hidden_source_for_x"

    # Nested Structure
    nested_obj = HiddenAttrDict(a="level_1", b={"level_2": {"level_3": "deep_value"}})
    assert nested_obj.b.level_2.level_3 == "deep_value"

    # List with Hidden Attributes
    list_obj = HiddenAttrDict(my_list=[{"x": "value1"}, {"y": "value2"}])
    assert list_obj.my_list[0].x == "value1"
    assert list_obj.my_list[1].y == "value2"

    # Recursively converted
    assert isinstance(list_obj.my_list, HiddenAttrList)

    list_obj.my_list.set_attribute(0, "src", "hidden_source_for_0")
    assert list_obj.my_list.get_attribute(0, "src") == "hidden_source_for_0"
