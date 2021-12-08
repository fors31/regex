from RPQ import loadgraph, runquery

g = loadgraph("papergraph_SW.txt") #un graphe de 12 noeuds et 20 arêtes

sol, visited, edgelist, bc = runquery(g,"green:1","<a>*<b><b>") #runquery( graphe, noeud de départ, expression regulière [attention syntaxe bizarre avec<>])

print(sol) # set des solutions
# les autres données (visited, edgelist, bc) ne sont pas utiles pour vous.

