from RPQ import loadgraph, runquery


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


def get_data_graph(er_list, graph, list_out_nodes):
    '''

    :param er_list: list of all de RE for the query
    :param graph: graph (dict) used for the guery (use loadgraph to convert)
    :param list_out_nodes: set of all outgoing nodes
    :return: a dict of {rule: [(origin_node, {response nodes})]}
    '''
    data_graph = dict()
    for node in graph:
        if node not in list_out_nodes:
            continue
        for er in er_list:
            data_graph.setdefault(er, [])
            sol, visited, edgelist, bc = runquery(graph, node, er_list[er])
            if len(sol) != 0:
                data_graph[er].append((node, sol))

    return data_graph


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


er_expanded = {"r1": "<a><b>*",
               "r2": "<a><b>*<c>",
               "r3": "<a><b>*<c><d>",
               "r4": "<b>+",
               "r5": "<b>*<c>",
               "r6": "<b>*<c><d>",
               "r7": "<d>"}

graph_filenames = ["graph_blue_2.txt","graph_green_2.txt", "graph_red_2.txt"]

g = loadgraph("graph_complet2.txt")
gblue = loadgraph("graph_blue_2.txt")
ggreen = loadgraph("graph_green_2.txt")
gred = loadgraph("graph_red_2.txt")
outnodes = get_all_out_nodes(graph_filenames)
outnodes.add("blue:1")

partial_result1 = get_data_graph(er_expanded, gblue, outnodes)

#print(partial_result1)

full_result = get_data_graph(er_expanded, gblue, outnodes).copy()

for graph in [ggreen, gred]:
     partial_result = get_data_graph(er_expanded, graph, outnodes)
     for key in partial_result:
         if len(partial_result[key]) > 0:
            full_result[key].append(partial_result[key][0])

#print(full_result)
# for key in full_result:
#      print(full_result[key])

#print(g)

new_graph = dict()

for key in full_result:
    for node in full_result[key]:
        new_graph.setdefault(node[0], list())
        for destination in node[1]:
            new_graph[node[0]].append((destination, key))

for key in new_graph:
    print(key, new_graph[key])
#print(new_graph)



result = get_outgoing_nodes("green", "Graph Green.txt")
red = get_outgoing_nodes("red", "Graph Red.txt")
test = get_incoming_nodes("red", "Graph Red.txt", "green", result)
#print(test)



