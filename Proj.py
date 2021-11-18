from RPQ import loadgraph, runquery, bfs
from parse import NFA, State
import re


def get_incoming_nodes(local_name, local_file, external_name, external_file):
    gin = loadgraph(local_file)
    #gout = loadgraph(external_file)
    node_in = local_name.lower()
    node_ext = external_name.lower()
    nodes = []
    for val in external_file:
        if val.split(":")[0] != node_in:
            continue
        else:
            if val.split(":")[0].lower() == node_in:
                nodes.append(node_ext + " " + val)
    return nodes


def get_outgoing_nodes( filename):
    g = loadgraph(filename)
    domain_name = list(g.keys())[0].split(":")[0]  # use the first node in the file to get the domain
    nodes_out = set()
    node_in = domain_name.lower()
    for key in g.keys():
        if key.split(":")[0].lower() != node_in:
            continue
        else:
            for value in g[key]:
                if value[0].split(":")[0].lower() != node_in:
                    nodes_out.add(value[0])
    return nodes_out


def get_data_responses(origin_er, graph, list_out_nodes):
    '''
    Returns a tuple with a data structure with responses to all the requests sent to the servers
    and a set of not filtered nodes
    :param origin_er: original regular expression used to filter non end nodes
    :param graph: graph (dict) used for the guery (use loadgraph to convert)
    :param list_out_nodes: set of all outgoing nodes
    :return: a dict of {rule: [(origin_node, {response nodes})]}
    '''
    data_graph = dict()
    er_list = expand_re(origin_er)
    end_state = get_last_state(er_list)
    not_filtered = set()
    for node in graph:
        if node not in list_out_nodes:
            continue
        for er in er_list:
            data_graph.setdefault(er, [])
            sol, visited, edgelist, bc = runquery(graph, node, er_list[er][2])
            res_nodes = set()
            for res_node in sol:
                if res_node in list_out_nodes or end_state == er_list[er][1]:
                    res_nodes.add(res_node)
                    if end_state == er_list[er][1]:
                        not_filtered.add(res_node)
            if len(res_nodes) != 0:
                data_graph[er].append((node, res_nodes))
    return data_graph, not_filtered


def get_data_graph(graph_list, origin_er, outnodes):
    '''

    :param graph_list: a list of all the graph where requests are sent
    :param origin_er: regular expression to use to find the endpoints
    :param outnodes: set of all outgoing nodes in all the servers
    :return: a dict of all the data in a graph format
    '''
    full_result, not_filtered_nodes = get_data_responses(origin_er, graph_list[0], outnodes)
    for graph in graph_list[1::]:
        partial_result, partial_not_filtered_nodes = get_data_responses(origin_er, graph, outnodes)
        for not_filtered_node in partial_not_filtered_nodes:
            not_filtered_nodes.add(not_filtered_node)
        for key in partial_result:
            if len(partial_result[key]) > 0:
                for result in partial_result[key]:
                    full_result[key].append(result)

    new_graph = dict()

    for key in full_result:
        for node in full_result[key]:
            new_graph.setdefault(node[0], list())
            for destination in node[1]:
                new_graph[node[0]].append((destination, key))
    for not_filtered_node in not_filtered_nodes: #add not filtered nodes to respect the format
        new_graph.setdefault(not_filtered_node, [])
    return new_graph

def get_all_out_nodes(list_of_graph):
    '''
    Use a list of filenames (graphs) to get all the outgoing nodes
    Returns a set of all outgoing nodes
    '''
    all_out_nodes = set()
    for graph in list_of_graph:
        nodes = get_outgoing_nodes(graph)
        all_out_nodes.update(list(nodes))
    return all_out_nodes


def expand_re(er):
    '''
    TODO: automate the process
    Uses a regular expression in a format like <a><b>*<c> and decomposes it
    :param re: regular expression to decompose
    :return: a dict of rule : (start state, end state, regular expression)
    '''
    er_expanded = {"r1": (0, 1, "<a><b>*"),
                   "r2": (0, 2, "<a><b>*<c>"),
                   "r3": (0, 3, "<a><b>*<c><d>"),
                   "r4": (1, 1, "<b>+"),
                   "r5": (1, 2, "<b>*<c>"),
                   "r6": (0, 3, "<b>*<c><d>"),
                   "r7": (2, 3, "<d>")}
    return er_expanded


def get_last_state(er_expanded):
    '''
    Gets the end state from the dict of rules
    :param er_expanded: dict of rules
    :return: the end state of the automata
    '''
    end = set()
    for key in er_expanded:
        end.add(er_expanded[key][1])
    return max(end)



er = "<a><b>*<c><d>"

graph_filenames = ["graph_blue_2.txt","graph_green_2.txt", "graph_red_2.txt"]

g = loadgraph("graph_complet2.txt")
gblue = loadgraph("graph_blue_2.txt")
ggreen = loadgraph("graph_green_2.txt")
gred = loadgraph("graph_red_2.txt")
outnodes = get_all_out_nodes(graph_filenames)
outnodes.add("blue:1")
graph_list = [gblue, ggreen, gred]


resultat = get_data_graph(graph_list, er, outnodes)
# for key in resultat:
# #     print(key, resultat[key])

State0 = State("0")
State1 = State("1")
State2 = State("2")
State3 = State("3")
State0.transitions = {"r1": State1, "r2": State2, "r3": State3}
State1.transitions = {"r4": State1, "r5": State2, "r6": State3}
State2.transitions = {"r7": State3}
State3.is_end = True
NFA1 = NFA(State0, State3)
NFA1.addstate(State1, set())
NFA1.addstate(State2, set())

test_graph = loadgraph("testing.txt")
#print(test_graph)
#print(resultat)
# for key in test_graph:
#     if key not in resultat:
#         print(key)

print(resultat)
results = bfs(resultat, NFA1, "blue:1")
print(results[0])
