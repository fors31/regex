def fcounts(alist):
    #dict of element:count in alist
    return [(k,alist.count(k)) for k in set(alist)]

def parse_MS_line(line):
    #parse the line giving results of multi-source query, given in the format: (a,b) (c,d) ...
    sols = line.split()
    lefts=[]
    rights=[]
    for spair in sols:
        pair_as_list = spair.strip('()').split(',')  
        lefts.append(pair_as_list[0])
        rights.append(pair_as_list[1])

        print "solutions=", len(sols)
    if len(sols)>0:
        mostleft = sorted(fcounts(lefts),key=lambda (a,b):b, reverse=True)[0]            
        print "most frequent left node:", mostleft    

def parse_1S_line(line):
    #parse the line giving results of a single-source query, given in the format: b c d ... (actual pairs are a,b a,c ad... see query to find out who is a
    sols = line.split()
    print "solutions=", len(sols)


def parsefile(thefile, singlesrc=True):
    with open(thefile) as resfile:
        mode =0 #starting
        for line in resfile:
            if line.startswith("query"):
                mode =1
                continue
            elif line.startswith("solution"):
                mode=2
                continue
            elif line.startswith("visited"):
                mode=3
                continue
    
            #ok here we're getting data
            if (mode==1):
                print line
                
            elif (mode==2):
                
                if(singlesrc):
                    parse_1S_line(line)
                else:
                    parse_MS_line(line)
                
            elif  (mode==3):
                vis = line.split()
                print "visited nodes", len(vis)
            

