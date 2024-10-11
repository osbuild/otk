import copy
import os
from unittest.mock import Mock

from otk.annotation import AnnotatedDict, AnnotatedList, AnnotatedInt, AnnotatedPath, AnnotatedNode

from otk.context import CommonContext
from otk.transform import process_include
from otk.traversal import State

# pylint has problems with class decorators
# pylint: disable=no-member


# pylint: disable=too-many-locals,R0915
def test_annotated_classes():
    # Attribute Access
    obj = AnnotatedDict({"a": "some_value", "sub": {"x": "sub_value"}, "sub2": "hello"})
    assert obj['a'].value == "some_value"
    assert obj['sub']['x'].value == "sub_value"

    # Hidden Attribute Access
    obj.annotations["src"] = "file_of_obj:1"
    obj['sub'].annotations["src"] = "file_of_sub:2"

    assert obj.annotations["src"] == "file_of_obj:1"
    assert obj['sub'].annotations["src"] == "file_of_sub:2"

    # deep copy
    obj2 = copy.deepcopy(obj)
    assert obj2['a'].value == "some_value"
    assert obj2['sub'].value['x'].value == "sub_value"
    assert obj2.annotations["src"] == "file_of_obj:1"
    assert obj2['sub'].annotations["src"] == "file_of_sub:2"

    obj['a'].annotations["src"] = "file_of_a_and_sub2:2"
    obj['sub2'].annotations["src"] = "file_of_a_and_sub2:10"

    # check squash "src"
    obj.squash_annotations(list(obj.value.values()))
    assert obj.annotations == {"src": "* file_of_a_and_sub2:2, 10\n* file_of_sub:2"}

    # Nested Structure
    nested_obj = AnnotatedDict({"a": "level_1", "b": {"level_2": {"level_3": "deep_value"}}})
    assert nested_obj['b']['level_2']['level_3'].value == "deep_value"

    # List with Hidden Attributes
    list_obj = AnnotatedDict({"my_list": [{"x": "value1"}, {"y": "value2"}]})
    assert list_obj['my_list'][0]['x'].value == "value1"
    assert list_obj['my_list'][1]['y'].value == "value2"

    # Recursively converted
    assert isinstance(list_obj['my_list'], AnnotatedList)

    list_obj['my_list'].annotations["src"] = "hidden_source_for_my_list:5"
    assert list_obj['my_list'].annotations["src"] == "hidden_source_for_my_list:5"

    # dict with all primitives
    dict_with_builtins = AnnotatedDict({"s": "string", "i": 5, "f": 0.5, "b": True})

    # set_annotation would fail on builtin types, so they seem to be converted correctly
    dict_with_builtins['s'].annotations["src"] = "hidden_source_for_string:1"
    dict_with_builtins['i'].annotations["src"] = "hidden_source_for_int:1"
    dict_with_builtins['f'].annotations["src"] = "hidden_source_for_float:1"
    dict_with_builtins['b'].annotations["src"] = "hidden_source_for_bool:1"

    # test add_source_attributes
    data = AnnotatedDict()
    mock_data = Mock(start_mark=Mock(line=0, column=10, name="myfilename"),
                     end_mark=Mock(line=0, column=10, name="myfilename"))
    # seems to be a "feature" in Mock() that name needs to be set separately to get a string
    mock_data.start_mark.name = "myfilename"
    mock_data.start_end.name = "myfilename"

    data.add_source_attributes(mock_data)
    assert data.annotations["src"] == "myfilename:1"

    # list iterator
    iter_test = AnnotatedList([1, 2, 3])
    iter_test[0].annotations["key"] = "value"
    iter_test[1].annotations["key"] = "value"
    iter_test[2].annotations["key"] = "value"
    for i in iter(iter_test):
        assert i.annotations["key"] == "value"
        assert isinstance(i, AnnotatedInt)

    # list append - not yet supported
    # iter_test.append(AnnotatedInt(4))
    # assert isinstance(iter_test[3], AnnotatedInt)

    # deepcopy of path in list

    p1 = AnnotatedPath("file1")
    p1.annotations["src"] = "src1"
    p2 = AnnotatedPath("file2")
    p2.annotations["src"] = "src2"
    list_of_paths = AnnotatedList([p1, p2])
    assert list_of_paths[0].annotations["src"] == "src1"
    assert list_of_paths[1].annotations["src"] == "src2"

    list_copy = copy.deepcopy(list_of_paths)
    assert list_copy[0].annotations["src"] == "src1"
    assert list_copy[1].annotations["src"] == "src2"


TEST_YAML = """\
otk.version: 1

otk.target.osbuild:
  list:
    - 1
    - 2
  dict:
   nested_dict:
    foo: bar
"""


def test_annotate(tmp_path):
    test_yaml_path = tmp_path / "test.yaml"
    test_yaml_path.write_text(TEST_YAML)

    # set cur dir - to get nice paths
    AnnotatedNode._basedirs = [tmp_path, os.path.curdir]

    ctx = CommonContext(target_requested="osbuild")
    state = State()
    tree = process_include(ctx, state, AnnotatedPath(test_yaml_path))

    assert tree.annotations["src"] == "test.yaml:1"
    assert tree.value["otk.target.osbuild"].annotations["src"] == "* test.yaml:3"
    assert tree.value["otk.target.osbuild"].value["list"].annotations["src"] == "test.yaml:4"
    assert tree.value["otk.target.osbuild"].value["list"].value[0].annotations["src"] == "test.yaml:5"
    assert tree.value["otk.target.osbuild"].value["dict"].annotations["src"] == "test.yaml:7"
