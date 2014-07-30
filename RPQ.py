from parse import Lexer, Parser, Token, State, NFA, Handler
import re



#from regex github project
def compile(p, debug = False):
    
    def print_tokens(tokens):
        for t in tokens:
            print(t)

    lexer = Lexer(p)
    parser = Parser(lexer)
    tokens = parser.parse()

    handler = Handler()
    
    if debug:
        print_tokens(tokens) 

    nfa_stack = []
    
    for t in tokens:
        handler.handlers[t.name](t, nfa_stack)
    
    assert len(nfa_stack) == 1
    return nfa_stack.pop() 


def loadgraph(gfname):
    '''
    load graph from file
    graph data structure: dict{ node:[(node2,label), (node3,label)...], node2:[] ...}
    '''
    grafile = open(gfname)
    thegraph= dict()
    cnt=0
    for line in grafile:
        cnt +=1
        if (cnt%1000==0):print cnt
        if (len(line)<=1):continue
        tup = line.split()
        node1,node2,label = tup[0],tup[1],tup[2]
        thegraph.setdefault(node1,[]).append((node2,label)) 
        thegraph.setdefault(node2,[])
    return thegraph

def bfs(graph, NFA, start):
    visited, queue = set(), [(start, NFA.start)]
    graphsolutions = set()
    while queue:
        vertex = queue.pop(0)
        if vertex not in visited:
            visited.add(vertex)
            vgraph,vautom = vertex        
            # this step to be modified to follow specific edge labels
            
            #if vertex is terminal, add to solution list
            if (vautom.is_end):
                graphsolutions.add(vgraph)
            
            #get epsilon-transitions
            eps_states= [(vgraph, veps) for veps in vautom.epsilon]
            trans_states =[]
            #get labeled transitions
            for (vg2,outlabel) in graph[vgraph]:
                if (vautom.transitions.has_key(outlabel)):
                    vautom2 = vautom.transitions[outlabel]
                    trans_states.append((vg2,vautom2))
            
            trans_states.extend(eps_states)
    
            queue.extend([s for s in trans_states if s not in visited])
            
    return graphsolutions, visited #set of graph nodes in terminal nodes of product automaton; list of visited nodes

def runquery (graph, startnode, regex):
    '''
    Run provided single-source query on provided graph; query =(startnode,regex)
    returns answers + set of visited nodes in the graph
    '''
    NFA = compile(regex)
    print "starting..."
    return bfs(graph,NFA,startnode)

def runMSquery(graph,regex):
    '''
    run provided query (regex only) on provided graph
    returns answers + set of visited nodes in the graph
    '''
    NFA = compile(regex)
    print "starting..."
    answers =[]
    visited = set()
    for startnode in graph:
        sol,vis = bfs(graph,NFA,startnode)    
        for s in sol:
            answers.append((startnode,s))
        if (len(vis)>1): #we necessarily visit the starting node, but let's say that doesn't count if we don't visit any other nodes from there 
            # we must make this distinction because with our naive approach we necessarily visit the full graph.
            visited.update(set([v1 for (v1,v2) in vis]))
    return answers, visited

def __main__():
    pass

def singlesource(gfile,qfile, outfile=None):
    '''
    run single-source queries from provided file on provided graph
    optionally output results to a third file
    '''
    # load the graph
    g= loadgraph(gfile)
    
    print "loaded graph"
    qf = open(qfile)
    if(outfile):
        outf = open(outfile, 'w', 4096)
    cnt=0
    for line in qf:
        cnt =+1
        if(cnt>3):break
        snode,regex =line.split()[0], line.split()[1]
        print "query:\n", snode, regex
        if (outfile):
            outf.write("query:\n"+snode+", "+regex+"\n")            
        sol, vis = runquery(g, snode, regex)
        vnodes = set([v1 for (v1,v2) in vis])
        if (outfile):
            outf.write("solution_nodes:\n")            
            outf.write(" ".join(sol)+"\n")
            outf.write("visited_nodes:\n")            
            outf.write(" ".join(vnodes)+ "\n")
        else:
            print "solutions:\n", sol
            print "visitednodes\n:", 
            if (len(vnodes)>30):
                print "("+str(len(vnodes))+ ")" 
            else:
                print vnodes
                
    if(outfile):
        outf.close()

def multisource(gfile, qfile, outfile=None):
    g= loadgraph(gfile)
    print "loaded graph"
    qf = open(qfile)
    if(outfile):
        outf = open(outfile, 'w', 4096)    
    #cnt=0
    for line in qf:
        #cnt =+1
        #if(cnt>3):break
        regex = line.strip()
        print "multi-source query:", regex
        if (outfile):
            outf.write("query:\n"+regex+"\n")                    
        sols, vnodes = runMSquery(g, regex)
        if (outfile):
            outf.write("solution_pairs:\n")            
            outf.write(" ".join(['('+v1+','+v2+')' for (v1,v2) in sols])+"\n")
            outf.write("visited_nodes:\n")            
            outf.write(" ".join(vnodes)+ "\n")
        else:
            print "solutions:\n", sol                    
            print "visitednodes\n:", 
            if (len(vnodes)>30):
                print "("+str(len(vnodes))+ ")" 
            else:
                print vnodes
                
    if(outfile):
        outf.close()  

def selectNodes(graph, elist):
    '''
    select all nodes from the given graph such that one of their outgoing edges is in the provided list
    graph format: dict node:[(node1,label1), (node2,label2), ...]
    '''
    matchingnodes =set()
    for k in graph.keys():
        outedges = [label for (node,label) in graph[k]]
        for e in outedges:
            if e in elist:
                matchingnodes.add(k)
                break
    return matchingnodes

def selectNodes2(graph, elist):
    '''
    select all nodes from the given graph such that one of their outgoing edges is in the provided list
    this version returns the total size of data assuming a up2p-like data model
    graph format: dict node:[(node1,label1), (node2,label2), ...]
    '''
    matchingnodes =[]
    for k in graph.keys():
        outedges = [label for (node,label) in graph[k]]
        for e in outedges:
            if e in elist:
                matchingnodes.append(len(graph[k]))
                break
    return matchingnodes


def selectEdges(graph, elist):
    '''
    select all EDGES from the given graph such that its label is in the provided list
    graph format: dict node:[(node1,label1), (node2,label2), ...]
    '''
    matchingedges =set()
    for k in graph.keys():
        matchingedges.update([(k,node,label) for (node,label) in graph[k] if label in elist])
        
    return matchingedges

    
def selectForS1(gfile,qfile,getnodes=True,outfile=None):
    #get a priori selectiveness of queries
    g= loadgraph(gfile)
    print "loaded graph"
    qf = open(qfile)
    if(outfile):
        outf = open(outfile, 'w', 4096)    
    #cnt=0
    
    for line in qf:
        #find all edges in the query
        alledges =re.findall('(?<=<).*?(?=>)',line)
        #go through the graph and find the nodes that we would retrieve to process the query
        reduced = list(set(alledges))
        #print "query:", line,
        #print "edge labels: ", reduced, '['+str(len(reduced))+'] distinct edge labels'
        if (getnodes):
            nodeset = selectNodes2(g,reduced)
            print "apriori nodeset size: ", len(nodeset), sum(nodeset) #here it's the sum of sizes
        else:
            nodeset = selectEdges(g,reduced)
            print "apriori edgeset size: ", len(nodeset)
    qf.close()
        



bio_graph = "alibaba.graph.txt"
samplegraph= "papergraph.txt"
sampleq = "testqueriespaper.txt"
sampleMS = "testMSqueries.txt"
randomqueries = "samplerandomqueries.txt"     
bio_queries = "bio_queries.txt"
bio_queries_1S = "bio_queries_single_src.txt"
#sampleMSqueries = "sampleMSqueries.txt"     
#multisource(bio_graph,bio_queries, "RPQ_bio_results.txt")
#singlesource(bio_graph,bio_queries_1S, "RPQ_bio_results_single.txt")