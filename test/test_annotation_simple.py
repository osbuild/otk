from otk.annotation import AnnotatedNode


def test_annotation_simple() -> None:
    raw_data = {"otk.version": "2"}
    test_data: AnnotatedNode[dict] = AnnotatedNode(raw_data)

    assert isinstance(test_data, AnnotatedNode)
    assert isinstance(test_data.value, dict)
    assert f"{test_data}" == "{'otk.version': '2'}"

    raw_data1 = {"otk.version": "2", "otk.target.osbuild": {"pipelines": [{"a": 1}]}}

    test_data1: AnnotatedNode[dict] = AnnotatedNode(raw_data1)
    test_data1.annotations["content_src"] = "file:1,4"

    test_data1.value["otk.target.osbuild"].annotations["src"] = "file:2"
    test_data1.value["otk.target.osbuild"].annotations["column"] = 1
    test_data1.value["otk.target.osbuild"].annotations["content_src"] = "file:3,4"

    test_data1.value['otk.version'].annotations["src"] = "file:1"
    test_data1.value['otk.version'].annotations["column"] = 13

    test_data1.value['otk.target.osbuild'].value['pipelines'].annotations["src"] = "file:3"
    test_data1.value['otk.target.osbuild'].value['pipelines'].value[0].annotations["src"] = "file:4"

    assert isinstance(test_data1, AnnotatedNode)
    assert isinstance(test_data1.value['otk.target.osbuild'].value, dict)
    assert isinstance(test_data1.value['otk.target.osbuild'].value['pipelines'].value, list)

    assert f"{test_data1}" == "{'otk.version': '2', 'otk.target.osbuild': {'pipelines': [{'a': 1}]}}"

#     out_data = yaml.dump(test_data1, Dumper=AnnotatedNodeDumper)
#     assert out_data == """- '### {''content_src'': ''file:1,4''}'
# - '### otk.version: {''src'': ''file:1'', ''column'': 13}'
# - otk.version: '2'
# - otk.target.osbuild:
#   - '### {''src'': ''file:2'', ''column'': 1, ''content_src'': ''file:3,4''}'
#   - pipelines:
#     - '### {''src'': ''file:3''}'
#     - '### [0] {''src'': ''file:4''}'
#     - - a: '1'
# """
