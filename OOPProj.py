from RPQ import loadgraph, runquery, compile, bfs
from parse import NFA, State
from SPARQLWrapper import SPARQLWrapper, JSON
import rdflib
from jinja2 import Environment, FileSystemLoader

file_loader = FileSystemLoader("SPARQL-Templates")
env = Environment(loader=file_loader)
template5 = env.get_template('abcdTemplate.txt')
abcdtest = template5.render(indomain = "green", outdomains = ["red", "blue"])
class Serveur:
    def __init__(self, name, domain, graph):
        self.name = name
        self.domain = domain
        self.graph = graph # File containing datagraph
        self.innodes = set()
        self.outnodes = set()
        self.data = {}

    def get_outgoing_nodes(self):
        '''
        Get all outgoing node from the server/file
        :return: a set of nodes
        '''
        # TODO Ajouter le SPARQL pour obtenir les noeuds sortants
        g = loadgraph(self.graph)
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

        # Print the get outnodes SPARQL request
        template = env.get_template("outnodes-template.j2")
        temp_render = template.render(domain=self.domain)
        print(temp_render)

        return nodes_out

    def get_server_response(self, expanded_re):
        '''
        Returns a tuple with a data structure with responses to all the requests sent to the servers
        and a set of not filtered nodes
        :param expanded_re: a dict of rules {rule : start_state, end_state, regex}
        :return: Tuple of a dict of {rule: [(origin_node, {response nodes})]} and a set of not filtered nodes
        '''
        # TODO Use in_nodes and expanded_re to get responses from the server
        data_graph = dict()
        not_filtered = set()
        for rule in expanded_re:
            data_graph.setdefault(rule, [])
            for node in self.innodes:
                sol, visited, edgelist, bc = runquery(loadgraph(self.graph), node, expanded_re[rule][2])

                res_nodes = set()
                for res_node in sol:
                    if res_node in self.outnodes or expanded_re[rule][1].is_end:
                        res_nodes.add(res_node)
                        if expanded_re[rule][1].is_end:
                            not_filtered.add(res_node)
                if len(res_nodes) != 0:
                    data_graph[rule].append((node, res_nodes))

        # Ajouter machins templates SPAQRL icitte
        template5 = env.get_template('abcdTemplate.txt')
        abcdtest = template5.render(indomain="green", outdomains=["red", "blue"])
        print(abcdtest)

        return data_graph, not_filtered


class Client:
    def __init__(self, name):
        self.name = name
        self.expanded_re = None
        self.knownServers = []
        self.start_node = ""

    def expand_re(self, regex):
        '''
        TODO: automate the process
        Uses a regular expression in a format like <a><b>*<c> and decomposes it
        Us
        :param regex: regular expression to decompose
        :return: a dict of rule : (start state, end state, regular expression),
                 the NFA's start state and a set of all the end states
        '''
        compiled_regex = compile(regex)

        # Get a list of all the states of the original regex from the NFA
        # Code borrowed from parse.py NFA.uglyprint()
        states = []
        visited, queue = set(), [compiled_regex.start]

        while queue:
            vertex = queue.pop(0)
            if vertex not in visited:
                visited.add(vertex)
                transitions = set()
                for k in vertex.transitions.keys():
                    trans = vertex.transitions[k]
                    states.append(trans)
                    if trans not in visited:
                        transitions.add(trans)

                transitions.update(vertex.epsilon)
                queue.extend([s for s in transitions if s not in visited])

        # Manual decomposition of the regex using states from the original regex NFA
        re_expanded = {"r1": (states[0], states[1], "<a><b>*"),
                       "r2": (states[0], states[2], "<a><b>*<c>"),
                       "r3": (states[0], states[3], "<a><b>*<c><d>"),
                       "r4": (states[1], states[1], "<b>+"),
                       "r5": (states[1], states[2], "<b>*<c>"),
                       "r6": (states[1], states[3], "<b>*<c><d>"),
                       "r7": (states[2], states[3], "<d>")}

        start_state = compiled_regex.start

        # Find all the end states in the NFA
        end_states = set()
        for state in states:
            if state.is_end is True:
                end_states.add(state)

        self.expanded_re = re_expanded, start_state, end_states

    def get_data_responses(self, server):
        '''
        Sends the query to the server object using the Serveur.get_server_response method
        :param server: Serveur instance used to send the query
        :return: a Tuple with dict format -> {rule : [(start_node, {set of end nodes})] and a set of not filtered nodes
        '''
        er_list, start_state, end_states = self.expanded_re
        response, not_filtered = server.get_server_response(er_list)

        return response, not_filtered

    def get_data_graph(self, graph_list):
        '''
        Get all the responses data structure from all the servers and merge then into a single graph
        :param graph_list: a list of all the graph where requests are sent
        :param origin_er: regular expression to use to find the endpoints
        :return: a dict of all the data in a graph format
        '''

        # Merge all the data_responses together
        full_result, not_filtered_nodes = self.get_data_responses(graph_list[0])
        for current_graph in graph_list[1::]:
            partial_result, partial_not_filtered_nodes = self.get_data_responses(current_graph)
            for not_filtered_node in partial_not_filtered_nodes:
                not_filtered_nodes.add(not_filtered_node)
            for key in partial_result:
                if len(partial_result[key]) > 0:
                    for result in partial_result[key]:
                        full_result[key].append(result)

        # Format the data_responses merged into a graph using the loadgraph format
        new_graph = dict()

        for key in full_result:
            for node in full_result[key]:
                new_graph.setdefault(node[0], list())
                for destination in node[1]:
                    new_graph[node[0]].append((destination, key))
        for not_filtered_node in not_filtered_nodes:  # add not filtered nodes to respect the loadgraph format
            new_graph.setdefault(not_filtered_node, [])

        return new_graph

    def get_server_out_nodes(self, server):
        '''
        Returns the outgoing nodes of a specified server, if said server exists in the knownServers list
        Otherwise, adds this server to the list of knownServers
        :param server: a single server for which you want the outgoing nodes
        '''
        outnodes = server.get_outgoing_nodes()
        if server.name not in self.knownServers:
            self.knownServers.update({server.name : (server.domain, {"outnodes": (outnodes)}, {"innodes" : ()})})
        else:
            self.knownServers[server.name][1]["outnodes"] = outnodes

    def get_innodes(self, server, outnodes_list):
        '''
        Gets all incoming nodes for a given server.
        :param server: The server for which you want to find the incoming nodes
        :param outnodes_list: Outnodes list for outside servers of the one you inquire about
        :return: Updates this client's knownServers innodes for the server inquired about
        '''
        all_nodes = set()
        for node in outnodes_list: # Check all outgoing nodes in the given list
            if server.domain in node: # If inquired server's domain appears in the outgoing nodes list iteration
                all_nodes.add(node)
        server.innodes = all_nodes # Update known incoming nodes list for specified server

    def get_all_out_nodes(self, list_of_servers):
        '''
        Use a list of filenames (graphs) to get all the outgoing nodes
        Returns a set of all outgoing nodes
        '''
        all_out_nodes = set()
        for server in list_of_servers:
            nodes = server.get_outgoing_nodes()
            all_out_nodes.update(list(nodes))
        return all_out_nodes

    def get_NFA(self):
        '''
        Builds an NFA using the State and NFA classes from parse.py
        :return: an NFA object
        '''

        list_of_states = []
        transitions = dict()
        rules = self.expanded_re[0]
        end_state = None

        # Creates a list of all the states from the expanded_re rules
        for rule in rules:
            for state in rules[rule][:2]:
                if state not in list_of_states:
                    list_of_states.append(state)

        # Get all the transitions for each State
        for rule in rules:
            transitions.setdefault(rules[rule][0], set())
            transitions[rules[rule][0]].add((rules[rule][1], rule))

        # Transform into a set of transition in dict and add them to the actual state
        for state in transitions:
            actual_transitions = {}
            for transition in transitions[state]:
                actual_transitions.setdefault(transition[1], transition[0])
            state.transitions = actual_transitions

        # Get first state
        start_state = list_of_states[0]
        list_of_states.remove(start_state)

        # Get last states
        for state in list_of_states:
            if state.is_end:
                end_state = state
                list_of_states.remove(state)

        # Set start and end states
        result_NFA = NFA(start_state, end_state)

        # Add all the states in between
        for inter_state in list_of_states:
            result_NFA.addstate(inter_state, set())

        return result_NFA

    def set_servers_in_out_nodes(self, list_of_servers):
        '''
        Sets the all the outnodes and innodes for all the Knownservers of the Client instance with the given responses
        :param list_of_servers: List of Serveur instances for the given Client
        :return: None
        '''
        # Add all outnodes for each client.knownservers
        for graph in list_of_servers:
            graph.outnodes = graph.get_outgoing_nodes()

        # Add all innodes for client.knownservers
        list_of_servers = list_of_servers.copy()
        for index, server in enumerate(self.knownServers):
            known_servers_temp = self.knownServers.copy()
            known_servers_temp.pop(index)
            temp_in_nodes = set()
            for temp_server in known_servers_temp:
                for node in temp_server.outnodes:
                    temp_in_nodes.add(node)
            current_server = list_of_servers.pop(0)
            self.get_innodes(current_server, temp_in_nodes)
            if server.domain in self.start_node: # Add start node to innode of starting server
                server.innodes.add(self.start_node)

    def initiate(self, list_of_servers, regex, start_node):
        '''
        Sets all the used data in the Client for the next steps
        :param list_of_servers: sets the list of servers in the Client object
        :param regex: string regex used to set the expanded regex in the Client object
        :param start_node: string node added to the innodes of the starting server
        :return:
        '''
        self.knownServers = list_of_servers
        self.expand_re(regex)
        self.start_node = start_node

    def run_distributed_query(self):
        '''
        Main method of the program
        Run a distributed query on the list of servers then run a local query on the resulting local graph
        :return:
        '''
        # Set all the in and out nodes
        self.set_servers_in_out_nodes(self.knownServers)

        # Get local graph with all the responses
        responses = self.get_data_graph(self.knownServers)

        # Create NFA with the expanded regex
        temp_NFA = self.get_NFA()

        # Run query on the local graph with the expanded regex NFA
        return bfs(responses, temp_NFA, self.start_node)


# ---- Test case ----

c1 = Client("clientnom")
s1 = Serveur("serveur1", "blue", "graph_blue_2.txt")
s2 = Serveur("serveur2", "green", "graph_green_2.txt")
s3 = Serveur("serveur3", "red", "graph_red_2.txt")
regex = "<a><b>*<c><d>"
graph_servers = [s1, s2, s3]

c1.initiate(graph_servers, regex, "blue:1")

results = c1.run_distributed_query()
print(results[0])

file_loader = FileSystemLoader('SPARQL-Templates')
env = Environment(loader=file_loader)




