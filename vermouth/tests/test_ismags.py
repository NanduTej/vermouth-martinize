# Copyright 2018 University of Groningen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Contains unittests for vermouth.ismags.
"""

# no-member because module networkx does indeed have a member isomorphism;
# redefined-outer-name because pylint does not like fixtures;
# pylint: disable=no-member, redefined-outer-name

import hypothesis.strategies as st
from hypothesis import given, note, settings

from hypothesis_networkx import graph_builder
import networkx as nx
import pytest
import vermouth.ismags

from .helper_functions import make_into_set


@pytest.fixture(params=[
    (
        [(0, dict(name='a')),
         (1, dict(name='a')),
         (2, dict(name='b')),
         (3, dict(name='b')),
         (4, dict(name='a')),
         (5, dict(name='a'))],
        [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]
    ),
    (
        range(1, 5),
        [(1, 2), (2, 4), (4, 3), (3, 1)]
    ),
    (
        [],
        [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (0, 6), (6, 7),
         (2, 8), (8, 9), (4, 10), (10, 11)]
    ),
])
def graphs(request):
    """
    Some simple, symmetric graphs
    """
    nodes, edges = request.param
    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)
    return graph


def test_symmetric_self_isomorphism(graphs):
    """
    Make sure that when considering symmetry, there is only one isomorphism
    between a graph and itself
    """
    ismags = vermouth.ismags.ISMAGS(graphs, graphs)
    iso = list(ismags.find_subgraphs(True))
    assert len(iso) == 1

    graph_matcher = nx.isomorphism.GraphMatcher(graphs, graphs)
    nx_answer = list(graph_matcher.isomorphisms_iter())
    assert make_into_set(iso) <= make_into_set(nx_answer)


def test_asymmetric_self_isomorphism(graphs):
    """
    Compare with reference implementation
    """
    ismags = vermouth.ismags.ISMAGS(graphs, graphs)
    ismags_answer = list(ismags.find_subgraphs(False))
    graph_matcher = nx.isomorphism.GraphMatcher(graphs, graphs)
    nx_answer = list(graph_matcher.isomorphisms_iter())
    assert make_into_set(ismags_answer) == make_into_set(nx_answer)


# no-value-for-parameter because `draw` is not explicitely passed;
# no-member because module networkx does indeed have a member isomorphism.
# pylint: disable=no-value-for-parameter, no-member


MAX_NODES = 10
ATTRNAMES = ['attr1', 'attr2']
NODE_DATA = st.dictionaries(keys=st.sampled_from(ATTRNAMES),
                            values=st.integers(min_value=0, max_value=MAX_NODES))

ATTRS = st.lists(st.sampled_from(ATTRNAMES), unique=True, min_size=0, max_size=2)
ISO_DATA = st.fixed_dictionaries({'atomname': st.integers(max_value=MAX_NODES, min_value=0),
                                  'element': st.integers(max_value=MAX_NODES, min_value=0)})

ISO_BUILDER = graph_builder(node_data=ISO_DATA, min_nodes=0, max_nodes=MAX_NODES,
                            node_keys=st.integers(max_value=MAX_NODES, min_value=0))


@settings(max_examples=500)
@given(graph=ISO_BUILDER, subgraph=ISO_BUILDER)
def test_asymmetric_isomorphism_nonmatch(graph, subgraph):
    """
    Test against networkx reference implementation using graphs that are
    probably not subgraphs without considering symmetry.
    """

    note(("Graph nodes", graph.nodes(data=True)))
    note(("Graph edges", graph.edges))
    note(("Subgraph nodes", subgraph.nodes(data=True)))
    note(("Subgraph edges", subgraph.edges))

    node_match = nx.isomorphism.categorical_node_match('element', None)
    matcher = nx.isomorphism.GraphMatcher(graph, subgraph, node_match=node_match)
    expected = make_into_set(matcher.subgraph_isomorphisms_iter())
    ismags = vermouth.ismags.ISMAGS(graph, subgraph, node_match=node_match)

    found = make_into_set(ismags.find_subgraphs(False))
    note(("Found", found))
    note(("Expected", expected))

    assert found == expected


@settings(max_examples=500)
@given(graph=ISO_BUILDER, subgraph=ISO_BUILDER)
def test_symmetric_isomorphism_nonmatch(graph, subgraph):
    """
    Test against networkx reference implementation using graphs that are
    probably not subgraphs considering symmetry.
    """

    note(("Graph nodes", graph.nodes(data=True)))
    note(("Graph edges", graph.edges))
    note(("Subgraph nodes", subgraph.nodes(data=True)))
    note(("Subgraph edges", subgraph.edges))

    node_match = nx.isomorphism.categorical_node_match('element', None)
    matcher = nx.isomorphism.GraphMatcher(graph, subgraph, node_match=node_match)
    expected = make_into_set(matcher.subgraph_isomorphisms_iter())
    ismags = vermouth.ismags.ISMAGS(graph, subgraph, node_match=node_match)

    found = make_into_set(ismags.find_subgraphs(True))
    note(("Found", found))
    note(("Expected", expected))

    assert found <= expected
    if found == expected and expected:
        assert ismags.analyze_symmetry() == ([], {})


@settings(max_examples=500)
@given(subgraph=ISO_BUILDER)
def test_hypo_symmetric_self_isomorphism(subgraph):
    """
    Make sure that when considering symmetry, there is only one isomorphism
    between a graph and itself
    """
    note(("Graph nodes", subgraph.nodes(data=True)))
    note(("Graph edges", subgraph.edges))

    node_match = nx.isomorphism.categorical_node_match('element', None)
    ismags = vermouth.ismags.ISMAGS(subgraph, subgraph, node_match=node_match)

    found = make_into_set(ismags.find_subgraphs(True))
    note(("Found", found))

    assert len(found) == 1


@settings(max_examples=500)
@given(st.data())
def test_asymmetric_isomorphism_match(data):
    """
    Test against networkx reference implementation using graphs that are
    subgraphs without considering symmetry.
    """

    graph = data.draw(ISO_BUILDER)
    nodes = data.draw(st.sets(st.sampled_from(list(graph.nodes)),
                              max_size=len(graph)))
    subgraph = graph.subgraph(nodes)

    note(("Graph nodes", graph.nodes(data=True)))
    note(("Graph edges", graph.edges))
    note(("Subgraph nodes", subgraph.nodes(data=True)))
    note(("Subgraph edges", subgraph.edges))

    node_match = nx.isomorphism.categorical_node_match('element', None)
    matcher = nx.isomorphism.GraphMatcher(graph, subgraph, node_match=node_match)
    expected = make_into_set(matcher.subgraph_isomorphisms_iter())
    ismags = vermouth.ismags.ISMAGS(graph, subgraph, node_match=node_match)

    found = make_into_set(ismags.find_subgraphs(False))
    note(("Found", found))
    note(("Expected", expected))

    assert found == expected


@settings(max_examples=500)
@given(st.data())
def test_symmetric_isomorphism_match(data):
    """
    Test against networkx reference implementation using graphs that are
    subgraphs considering symmetry.
    """

    graph = data.draw(ISO_BUILDER)
    nodes = data.draw(st.sets(st.sampled_from(list(graph.nodes)),
                              max_size=len(graph)))
    subgraph = graph.subgraph(nodes)

    note(("Graph nodes", graph.nodes(data=True)))
    note(("Graph edges", graph.edges))
    note(("Subgraph nodes", subgraph.nodes(data=True)))
    note(("Subgraph edges", subgraph.edges))

    node_match = nx.isomorphism.categorical_node_match('element', None)
    matcher = nx.isomorphism.GraphMatcher(graph, subgraph, node_match=node_match)
    expected = make_into_set(matcher.subgraph_isomorphisms_iter())
    ismags = vermouth.ismags.ISMAGS(graph, subgraph, node_match=node_match)

    found = make_into_set(ismags.find_subgraphs(True))
    note(("Found", found))
    note(("Expected", expected))

    note(found - expected)

    assert found <= expected
    if found == expected and expected:
        assert ismags.analyze_symmetry() == ([], {})
