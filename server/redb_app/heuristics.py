"""
Heuristics for comparing attribute instances.
"""

# standard library imports
from itertools import product
from difflib import SequenceMatcher
from utils import CliquerGraph

MAX_GRAPH_COMP_SIZE = 120
MINIMUM_NODE_WEIGHT = 0.75

ITYPES_WEIGHT = 0.8
STRINGS_WEIGHT = 0.1
CALLS_WEIGHT = 0.1
IMMS_WEIGHT = 0


class Heuristic:
    """ Represents a single attribute. """
    def __init__(self, instnace_1, instance_2):
        """
        Initializes Heuristic class with two attribute instances and computes
        similarity grade with regard to the heuristic and attribute.
        """
        pass

    def ratio(self):
        """ Retrieves Results """
        pass


class DictionarySimilarity(Heuristic):
    """
    Grades dictionaries similarity.
    """
    def __init__(self, dict1, dict2):
        self.a_dict = dict1
        self.b_dict = dict2
        self._ratio = None

    def ratio(self):
        if (self._ratio == None):
            a_keys = set(self.a_dict.keys())
            b_keys = set(self.b_dict.keys())
            c_s = a_keys.union(b_keys)

            f_sum = 0
            d_sum = 0
            for c in c_s:
                a_value = 0
                if (c in a_keys):
                    a_value = int(self.a_dict[c])
                b_value = 0
                if (c in b_keys):
                    b_value = int(self.b_dict[c])

                minimum = (float)(min(a_value, b_value))
                maximum = (float)(max(a_value, b_value))
                f_sum += a_value + b_value
                d_sum += (a_value + b_value) * (minimum / maximum)

            if (f_sum):
                self._ratio = d_sum / f_sum
            else:
                self._ratio = 1.0
        return self._ratio


class BlockSimilarity(Heuristic):
    def __init__(self, block_1, block_2):
        self.block_1 = block_1
        self.block_2 = block_2
        self._ratio = None

    def ratio(self):
        if self.block_1 == self.block_2:
            return 1.0
        return (ITYPES_WEIGHT * self.itypes_similarity() + \
                STRINGS_WEIGHT * self.strings_similarity() + \
                CALLS_WEIGHT * self.call_similarity() + \
                IMMS_WEIGHT * self.immediates_similarity())

    def itypes_similarity(self):
        return SequenceMatcher(self.block_1.itypes,
                               self.block_2.itypes).ratio()

    def strings_similarity(self):
        return SequenceMatcher(self.block_1.strings,
                               self.block_2.strings).ratio()

    def call_similarity(self):
        return SequenceMatcher(self.block_1.calls,
                               self.block_2.calls).ratio()

    def immediates_similarity(self):
        return SequenceMatcher(self.block_1.immediates,
                               self.block_2.immediates).ratio()


class GraphSimilarity(Heuristic):
    def __init__(self, graph_1, graph_2):
        self.graph_1 = graph_1
        self.graph_2 = graph_2

    def ratio(self):
        if self.graph_1 == self.graph_2:
            return 1.0
        elif self.graph_1.edges == self.graph_2.edges:
            return self.blocks_similarity()
        else:
            return self.graph_similarity()

    def blocks_similarity(self):
        f_sum = 0
        d_sum = 0
        for block_num in range(len(self.graph_1.blocks)):
            block_1 = self.graph_1.blocks[block_num]
            block_2 = self.graph_2.blocks[block_num]
            ratio = BlockSimilarity(a=block_1, b=block_2).ratio()

            len_1 = float(len(block_1.itypes))
            len_2 = float(len(block_2.itypes))

            f_sum += (len_1 + len_2)
            d_sum += (len_1 + len_2) * ratio
        return d_sum / f_sum

    def graph_similarity(self):
        nodes = product(range(len(self.graph_1.blocks)),
                        range(len(self.graph_2.blocks)))
        filtered_nodes = []
        filtered_weights = []
        for node in nodes:
            weight = BlockSimilarity(self.graph_1.blocks[node[0]],
                                     self.graph_2.blocks[node[1]]).ratio()
            print weight
            if weight > MINIMUM_NODE_WEIGHT:
                filtered_nodes.append(node)
                filtered_weights.append(int(weight * 1000))

        num_of_nodes = len(filtered_nodes)
        print num_of_nodes
        graph = CliquerGraph(num_of_nodes)

        for node_num in range(num_of_nodes):
            graph.set_vertex_weight(node_num, filtered_weights[node_num])

        for x in range(num_of_nodes):
            for y in range(num_of_nodes):
                (i, s) = filtered_nodes[x]
                (j, t) = filtered_nodes[y]
                if s != t and i != j:
                    if ((((i, j) in self.graph_1.edges) and
                         ((s, t) in self.graph_2.edges)) or
                        (((i, j) not in self.graph_1.edges) and
                         ((s, t) not in self.graph_2.edges))):
                        graph.add_edge(x, y)
        size = float(graph.clique_max_size())
        return size / (len(self.graph_1.blocks) + \
                        len(self.graph_2.blocks) - size)
