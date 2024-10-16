import copy
from unittest.mock import Mock

from otk.annotation import AnnotatedDict, AnnotatedList, AnnotatedStr, AnnotatedInt, AnnotatedPath, AnnotatedBase

from otk.context import CommonContext
from otk.transform import process_include
from otk.traversal import State

# pylint has problems with class decorators
# pylint: disable=no-member


# pylint: disable=too-many-locals,R0915
def test_annotated_classes():
    # Attribute Access
    obj = AnnotatedDict(a="some_value", sub={"x": "sub_value"}, sub2="hello")
    assert obj['a'] == "some_value"
    assert obj['sub']['x'] == "sub_value"

    # Hidden Attribute Access
    obj.set_annotation("src", "file_of_obj:1")
    obj['sub'].set_annotation("src", "file_of_sub:2")

    assert obj.get_annotation("src") == "file_of_obj:1"
    assert obj['sub'].get_annotation("src") == "file_of_sub:2"

    # deep copy
    obj2 = copy.deepcopy(obj)
    assert obj2['a'] == "some_value"
    assert obj2['sub']['x'] == "sub_value"
    assert obj2.get_annotation("src") == "file_of_obj:1"
    assert obj2['sub'].get_annotation("src") == "file_of_sub:2"

    obj['a'].set_annotation("src", "file_of_a_and_sub2:2")
    obj['sub2'].set_annotation("src", "file_of_a_and_sub2:10")

    # check squash "src"
    assert obj.squash_annotations(list(obj.values())) == {"src": "* file_of_a_and_sub2:2, 10\n* file_of_sub:2"}

    # Nested Structure
    nested_obj = AnnotatedDict(a="level_1", b={"level_2": {"level_3": "deep_value"}})
    assert nested_obj['b']['level_2']['level_3'] == "deep_value"

    # List with Hidden Attributes
    list_obj = AnnotatedDict(my_list=[{"x": "value1"}, {"y": "value2"}])
    assert list_obj['my_list'][0]['x'] == "value1"
    assert list_obj['my_list'][1]['y'] == "value2"

    # Recursively converted
    assert isinstance(list_obj['my_list'], AnnotatedList)

    list_obj['my_list'].set_annotation("src", "hidden_source_for_my_list:5")
    assert list_obj['my_list'].get_annotation("src") == "hidden_source_for_my_list:5"

    # dict with all primitives
    dict_with_builtins = AnnotatedDict(s="string", i=5, f=0.5, b=True)

    # set_annotation would fail on builtin types
    dict_with_builtins['s'].set_annotation("src", "hidden_source_for_string:1")
    dict_with_builtins['i'].set_annotation("src", "hidden_source_for_int:1")
    dict_with_builtins['f'].set_annotation("src", "hidden_source_for_float:1")
    dict_with_builtins['b'].set_annotation("src", "hidden_source_for_bool:1")

    # still behave like builtins
    assert isinstance(dict_with_builtins['s'], str)
    assert isinstance(dict_with_builtins['i'], int)
    assert isinstance(dict_with_builtins['f'], float)
    assert isinstance(dict_with_builtins['b'], bool)

    # special conversion test - pyyaml needs "bool" to pass "var is True"
    # which does not apply to AnnotatedBase, so we need to convert
    dumped = AnnotatedBase.deep_dump(dict_with_builtins)
    assert dumped['b'] is True
    assert dumped['b']

    # test builtin operations
    s1 = AnnotatedStr("s1")
    s2 = AnnotatedStr("s2")
    s1.set_annotation("src", "hidden_source_for_strings:1")
    s2.set_annotation("src", "hidden_source_for_strings:2")

    s3 = s1 + s2
    assert s3 == "s1s2"
    assert s3.get_annotation("src") == "* hidden_source_for_strings:1, 2"

    s3 = s1 + "_hello"
    assert s3 == "s1_hello"
    src = s3.get_annotation("src")
    assert src == "* hidden_source_for_strings:1"

    s3 = "hello_" + s2
    assert s3 == "hello_s2"
    src = s3.get_annotation("src")
    assert src == "* hidden_source_for_strings:2"

    s2 += "_hello"
    assert s2 == "s2_hello"
    src = s2.get_annotation("src")
    assert src == "* hidden_source_for_strings:2"

    string = "test_"
    string += s1
    assert string == "test_s1"
    src = string.get_annotation("src")
    assert src == "* hidden_source_for_strings:1"

    # test add_source_attributes
    data = AnnotatedDict()
    mock_data = Mock(start_mark=Mock(line=0, column=10, name="myfilename"),
                     end_mark=Mock(line=0, column=10, name="myfilename"))
    # seems to be a "feature" in Mock() that name needs to be set separately to get a string
    mock_data.start_mark.name = "myfilename"
    mock_data.start_end.name = "myfilename"
    data.add_source_attributes(mock_data)
    assert data.get_annotation("src") == "myfilename:1"

    # list iterator
    iter_test = AnnotatedList([1, 2, 3])
    iter_test[0].set_annotation("key", "value")
    iter_test[1].set_annotation("key", "value")
    iter_test[2].set_annotation("key", "value")
    for i in iter(iter_test):
        assert i.get_annotation("key") == "value"
        assert isinstance(i, AnnotatedInt)

    # list append
    iter_test.append(AnnotatedInt(4))
    assert isinstance(iter_test[3], AnnotatedInt)

    # deepcopy of path in list

    p1 = AnnotatedPath("file1")
    p1.set_annotation("src", "src1")
    p2 = AnnotatedPath("file2")
    p2.set_annotation("src", "src2")
    list_of_paths = AnnotatedList([p1, p2])
    assert list_of_paths[0].get_annotation("src") == "src1"
    assert list_of_paths[1].get_annotation("src") == "src2"

    list_copy = copy.deepcopy(list_of_paths)
    assert list_copy[0].get_annotation("src") == "src1"
    assert list_copy[1].get_annotation("src") == "src2"

    # TBD test str(AnnotatedInt())

    # TBD test json.dumps(sample_tree, indent=2)


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
    AnnotatedBase._basedir = tmp_path

    ctx = CommonContext(target_requested="osbuild")
    state = State()
    tree = process_include(ctx, state, test_yaml_path)

    assert tree.get_annotation("src") == "test.yaml:1"
    assert tree["otk.target.osbuild"].get_annotation("src") == "test.yaml:3"
    assert tree["otk.target.osbuild"]["list"].get_annotation("src") == "test.yaml:4"
    assert tree["otk.target.osbuild"]["list"][0].get_annotation("src") == "test.yaml:5"
    assert tree["otk.target.osbuild"]["dict"].get_annotation("src") == "test.yaml:7"
