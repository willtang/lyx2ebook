from rp import rp
import re

def main():
    g = open('lyx.grammar' , 'r')
    rule = g.readlines()
    
    f = open('test.lyx', 'r')
    content = f.read()
    
    lyx = rp.match(rule, content)
    
    if lyx == None:
        print "Error in parsing."
        return
    
    exec(lyx.code)
    
    print lyx
    
    return

if __name__ == '__main__':
    main()
