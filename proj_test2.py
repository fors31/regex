from RPQ import loadgraph, runquery, bfs
from parse import NFA, State
import re


def get_outgoing_nodes(filename):
    g = loadgraph(filename)
    domain_name = list(g.keys())[0].split(":")[0]
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
    :return: a dict of rule : regular expression
    '''
    er_expanded = {"r1": (0, 0, "<a>+"),       # 0-0
                   "r2": (0, 1, "<a>*<b>"),    # 0-1
                   "r3": (0, 2, "<a>*<b><b>"), # 0-2
                   "r4": (1, 2, "<b>")         # 1-2
                   }
    return er_expanded


def get_last_state(er_expanded):
    end = set()
    for key in er_expanded:
        end.add(er_expanded[key][1])
    return max(end)


'''----------------------------------------'''
'''Testing another graph'''

g1 = loadgraph("papergraph_SW.txt")
gblue1 = loadgraph("Graph Blue.txt")
ggreen1 = loadgraph("Graph Green.txt")
gred1 = loadgraph("Graph Red.txt")
graph_filenames1 = ["Graph Blue.txt", "Graph Green.txt", "Graph Red.txt"]
outnodes1 = get_all_out_nodes(graph_filenames1)
outnodes1.add("green:1")
graph_list1 = [gblue1, ggreen1, gred1]

er = "<a>*<b><b>"

resultat1 = get_data_graph(graph_list1, er, outnodes1)

State01 = State("0")
State11 = State("1")
State21 = State("2")
State01.transitions = {"r1": State01, "r2": State11, "r3": State21}
State11.transitions = {"r4": State21}
State21.is_end = True
NFA11 = NFA(State01, State21)
NFA11.addstate(State11, set())

#NFA11.uglyprint()

results1 = bfs(resultat1, NFA11, "green:1")
print(results1[0])

g = loadgraph("papergraph_SW.txt") #un graphe de 12 noeuds et 20 arêtes

sol, visited, edgelist, bc = runquery(g,"green:1","<a>*<b><b>") #runquery( graphe, noeud de départ, expression regulière [attention syntaxe bizarre avec<>])

#print(sol) # set des solutions

#print(get_last_state(expand_re(er)))