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


result = get_outgoing_nodes("green", "Graph Green.txt")
red = get_outgoing_nodes("red", "Graph Red.txt")
test = get_incoming_nodes("red", "Graph Red.txt", "green", result)
print(test)
