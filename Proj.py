from RPQ import loadgraph, runquery
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


def get_outgoing_nodes(domain_name, filename):
    g = loadgraph(filename)
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


def get_data_responses(origin_er, er_list, graph, list_out_nodes):
    '''
    Returns a data structure with responses to all the requests sent to the servers
    :param er: original regular expression used to filter non end nodes
    :param er_list: list of all de RE for the query
    :param graph: graph (dict) used for the guery (use loadgraph to convert)
    :param list_out_nodes: set of all outgoing nodes
    :return: a dict of {rule: [(origin_node, {response nodes})]}
    '''
    filt = filter_branch(origin_er)
    data_graph = dict()
    for node in graph:
        if node not in list_out_nodes:
            continue
        for er in er_list:
            data_graph.setdefault(er, [])
            sol, visited, edgelist, bc = runquery(graph, node, er_list[er])
            res_nodes = set()
            for res_node in sol:
                if res_node in list_out_nodes or filt in er_list[er]:
                    res_nodes.add(res_node)
            if len(res_nodes) != 0:
                data_graph[er].append((node, res_nodes))

    return data_graph

def get_data_graph(graph_list, origin_er, er_list, outnodes):
    full_result = get_data_responses(origin_er, er_list, graph_list[0], outnodes).copy()
    for graph in graph_list[1::]:
        partial_result = get_data_responses(origin_er, er_list, graph, outnodes)
        for key in partial_result:
            if len(partial_result[key]) > 0:
                full_result[key].append(partial_result[key][0])

    new_graph = dict()

    for key in full_result:
        for node in full_result[key]:
            new_graph.setdefault(node[0], list())
            for destination in node[1]:
                new_graph[node[0]].append((destination, key))

    return new_graph

def get_all_out_nodes(list_of_graph):
    '''
    Use a list of filenames (graphs) to get all the outgoing nodes
    Returns a set of all outgoing nodes
    '''
    all_out_nodes = set()
    for graph in list_of_graph:
        nodes = get_outgoing_nodes(graph.split("_")[1], graph)
        all_out_nodes.update(list(nodes))
    return all_out_nodes


def expand_re(er):
    '''
    TODO: automate the process
    Uses a regular expression in a format like <a><b>*<c> and decomposes it
    :param re: regular expression to decompose
    :return: a dict of rule : regular expression
    '''
    er_expanded = {"r1": "<a><b>*",
                   "r2": "<a><b>*<c>",
                   "r3": "<a><b>*<c><d>",
                   "r4": "<b>+",
                   "r5": "<b>*<c>",
                   "r6": "<b>*<c><d>",
                   "r7": "<d>"}
    return er_expanded


def filter_branch(er):
    '''
    Gets the last element of a regular expression (last branch)
    Used to filter results
    :param er: regular expression in a format like <a><b>*<c><d>
    :return: a string of the last element of the regular expression
    '''
    filt = re.findall('<\/?(.|\s|\S)*?>', er)
    return "<"+filt[len(filt)-1]+">"


er = "<a><b>*<c><d>"
filtered_er = filter_branch(er)

graph_filenames = ["graph_blue_2.txt","graph_green_2.txt", "graph_red_2.txt"]

g = loadgraph("graph_complet2.txt")
gblue = loadgraph("graph_blue_2.txt")
ggreen = loadgraph("graph_green_2.txt")
gred = loadgraph("graph_red_2.txt")
outnodes = get_all_out_nodes(graph_filenames)
outnodes.add("blue:1")
graph_list = [gblue, ggreen, gred]


resultat = get_data_graph(graph_list, er, expand_re(None), outnodes)
for key in resultat:
    print(key, resultat[key])





