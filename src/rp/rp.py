#lparis45@gmail.com
#
#copyright 2008 under the GNU General Public License
#

""" simple parser using rules defined in EBNF format

This module allows you to parse string according rules
you defined in EBNF format (light)

You use it as the re module:

    rp.match(rule,'string to be parsed') 
    
    Result: RP Object  when parsing is ok, 
                       else None
    
    where:
        rule is a list of rules definitions
        
        ex:  rule= ['main      ::= 'SELECT field FROM table' ,
                    'field     ::= alphanum*      ',
                    'alphanum  ::= r"[A-Za-z0-9]" ',
                    'table     ::= alphanum*      ' ] 
        
For more details read the rp.doc
"""

import re,string,shlex

__version__='0.91'
#0.91    2009/01  appending re.DOTALL to parsing $vars in interpret,
#                    as sometimes, \n exists !!!
#                 remove the strip of string
#                 ignore trailing blanks at the end of parsing
#                 take into account python reserved words

def compile(rule):
    ret=RP()
    ret.compile(rule)
    return ret

def match(rule,thestr):
    """ match the string against the rule """
    return compile(rule).match(thestr)

#==================================== internal code ==========================        
RESERVED={'and':'',         #0.91
          'as':'',
          'assert':'',
          'break':'',
          'class':'',
          'continue':'',
          'def':'',
          'del':'',
          'elif':'',
          'else':'',
          'except':'',
          'exec':'',
          'finally':'',
          'for':'',
          'from':'',
          'global':'',
          'if':'',
          'import':'',
          'in':'',
          'is':'',
          'lambda':'',
          'not':'',
          'or':'',
          'pass':'',
          'print':'',
          'raise':'',
          'return':'',
          'try':'',
          'while':'',
          'with':'',
          'yield':'',
    }
class _Tokenizer:
    """ class representing the string to parse """
    def __init__(self, string,rp):
        """ set default values for string """
        self.string = string
        self.index = 0
        self.depth=0
        self.maxscan=0
        self.rp=rp
    def peek(self):
        """ peek current character in string, without consume it """
        try: 
            this = self.string[self.index]
        except Exception:
            this=''
        #print 'peeked:',this
        return this
    def read(self):
        """ read current character, and increment cursor """
        this = self.peek()
        self.index+=1
        self.maxscan=max(self.maxscan,self.index)
        return this
    def getString(self,ptr):
        """ return the parsed substring (ptr is the start point) """
        return self.string[ptr:self.index]
    def getRemaining(self):
        """ returns the remaining part of string not parsed """
        return self.string[self.index:]
    def removeBlanks(self):
        """ removed blanks of string before parsing rule, terminal or regular character
        this function could be desactivated using rp.IGNORE_BLANKS
        """
        if self.rp.ignore_blanks:
            while self.peek()==' ':
                self.read()
        return self.index
    def reset(self,ptr=0):
        """ reset pointer when rule parsing is ko """
        self.index=ptr
    def getIndent(self,_down,_str='.'):
        """ returns string of ... for  debugging purposing """
        if _down:
            _str=_str*self.depth
            self.depth+=1
        else:
            self.depth-=1
            _str=_str*self.depth
        return _str
        
class _RpRule:
    """ Class that defines rule """
    def __init__(self,name,_rp):
        self.name=name
        self.definitions=[]
        self.rp=_rp
    def addDefinition(self,aDef):
        """ add a definition to the rule """
        self.definitions.append(aDef)
    def match(self,_tk):
        """ match the string against the rule 
        Usually, this method is only used for the main rule 
        (the first rule defined)
        """
        for init in self.rp.code_init:
            if self.rp.execute_code:
                exec(init,self.rp.vals)
            self.rp.code_array.append(init)
        _tk=_Tokenizer(_tk,self.rp)    #0.91
        self.scanMax=0
        self._parse(_tk)
        len1=_tk.index#+1
        if self.rp.ignore_blanks:           #0.91
            len2=len(_tk.string.rstrip())   #0.91
        else:                               #0.91
            len2=len(_tk.string)
        if len1<len2:
            self.rp.stringError=('-'*(_tk.maxscan)+'^')
            if self.rp.verbose: 
                print _tk.string
                print self.rp.stringError
        else:
            for post in self.rp.code_post:
                if self.rp.execute_code:
                    exec(post,self.rp.vals)
                self.rp.code_array.append(post)
            codestr=''
            for x in self.rp.code_array:
                codestr+=x+'\n'
            self.rp.code=codestr
        return len1>=len2
    def _parse(self,_tk,mult='',n_val=None):
        """ parse the string against the rule """
        if self.rp.verbose: print _tk.getIndent(True)+'Parsing rule: "'+self.name+'" for string:"'+_tk.getRemaining()+'"'
        ret=-1
        _top=_tk.index
        _top2=_tk.removeBlanks()
        if mult=='' or mult=='?':
            for d in self.definitions:
                ret=d._parse(_tk)
                if ret>=0: break # Leave loop, this rule is OK !!
            if ret<0 and mult=='?':
                ret=0            # rule ok or not, no problem
        else:
            fullret=-1
            #
            # try to make a parsing 
            #
            for d in self.definitions:
                ret=d._parse(_tk)
                if ret>0: 
                    fullret=ret
                    break #Leave for loop as this rule is OK
            #
            # if previous parsing is ok, then go for infinite...
            #     
            while ret>0:
                for d in self.definitions:
                    ret=d._parse(_tk)
                    if ret>0:
                        break #Leave for loop as this rule is OK
            #
            # now, check according '+' or '*'
            #
            ret=fullret
            if ret<0 and mult=='*':
                ret=0
        _retstr='' 
        _retindent='.'
        if ret>=0:
            self.rp.vals[self.name]=_tk.getString(_top2)
            _retstr=_tk.getString(_top2)
            if ret>0: _retindent='<'
        elif ret<0:
            _tk.reset(_top)
        if self.rp.verbose: print _tk.getIndent(False,_retindent)+'Parsed rule :"'+self.name+'" - value="'+_retstr+'"'
        return ret

class _RpDefinition:
    """ Class containing definitions (rule, terminal,...) """
    def __init__(self,aDef,_rp,code=''):
        """ in init, we make:
         - scan the definitions to create relative objects
             such as Rule, Terminal, Regular.
         - acquire the future to be executed
        """ 
        self.rp=_rp
        self.definition=self._scan(aDef)
        self.code=code
    def _addcode(self,code):
        """ add code statement to the current definition """
        self.code+='\n'+code
    def _parse(self,_tk,mult=''):
        """ parse the definition:
           - loop on all items of definition 
           - and call appropriate objet._parse 
              (Rule,Terminal,Regular)
        """
        ret=-1
        _top=_tk.index
        fullret=-1
        for _i,_def in enumerate(self.definition):
            #d,mult,notrule in self.definition:
            d,mult,notrule=_def
            if notrule: break  #Quit this loop as this this the end !!
            n_d,n_mult,n_notrule,n_val=None,None,None,None
            if _i<(len(self.definition)-1):
                n_d,n_mult,n_notrule=self.definition[_i+1]
                if n_notrule:
                    if isinstance(n_d,_RpRule) and self.rp.vals.has_key(n_d.name):
                        n_val=self.rp.vals[n_d.name]
            try:
                ret=d._parse(_tk,mult,n_val)
                if ret>0:
                    fullret=max(fullret,ret)
            except IndexError,err:
                print '+++',err
                ret=-1
                _tk.getIndent(False) # Just to adjust indentation
                break
            if ret<0:
                fullret=-1
                break # one definition is not OK
        ret=fullret
        if ret<0:
            _tk.reset(_top)
        elif ret>0:
            #
            # this definition is successfully parsed, 
            # so, relative code could be interpreted.
            #
            self._interpretCode()
        return ret
    
    def _quote_split(self,str):
        """ Split string with respect to double quotation mark """
        result=[]
        sp = str.split()
        if len(sp) == 1:
            return sp
        
        for i in range(len(sp)-1):
            if sp[i].find("\"") != -1 and sp[i+1].find("\"") != -1:
                result.append(sp[i] + " " + sp[i+1])
                i+=1
            else:
                if i != len(sp)-2:
                    result.append(sp[i])
                else:
                    result.append(sp[i])
                    result.append(sp[i+1])
        
        return result
            
    def _scan(self,adef):
        """ scan definition to create objects """
        definition=[]
        #for a in adef.split():
        for a in self._quote_split(adef):
            mult=''
            m=re.match(r'([^\+\?\*]*)(.?)$',a)
            if m==None:
                if len(a)>2 and (a[0:3]=='"+"' or a[0:3]=='"?"' or a[0:3]=='"*"'):
                    key=a[0:3]
                    mult=a[3:]
                elif len(a)>2 and ( a[0:4]=='"**"' or a[0:4]=='"+="' or a[0:4]=='"*="'):
                    key=a[0:4]
                    mult=a[4:]
                elif len(a)>2 and ( a[0:5]=='"**="'):
                    key=a[0:5]
                    mult=a[5:]
                else:
                    raise Exception('Invalid definition: %s in %s' % (a,adef))
            else:
                key=m.group(1)
                mult=m.group(2)
            notrule=False
            #
            # "x"..."y"  ==> Regular expression
            #
            if key.find('"..."')>=2:
                m2=re.match('"(.)"\.{3}"(.)"',key)
                if m2==None:
                    raise Exception , 'Invalid expression:'+key
                a1=_RpRegular('['+m2.group(1)+'-'+m2.group(2)+']',self.rp)
            #
            # "xxx"  == Terminal 
            #
            elif key[0]=='"' and key[-1]=='"':
                a1=_RpTerminal(key[1:-1],self.rp)
            #
            # "xxxx   ==> Exception (" is missing)    
            #
            elif key[0]=='"' and key[-1]!='"':
                raise Exception('End " is missing: %s in %s' % (a,adef))
            #
            # r"xxxx"  == Regular expression
            #
            elif key[0]=='r' and key[1]=='"' and key[-1]=='"':
                a1=_RpRegular(key[2:-1],self.rp)
            #
            # lower_case  == Rule 
            #
            elif key.islower():
                if key[0]=='^':
                    notrule=True
                    key=key[1:]
                if self.rp.rules.has_key(key):
                    a1=self.rp.rules[key]
                else:
                    a1=_RpRule(key,self.rp)
                    self.rp.rules[key]=a1
            #
            # ..else   == Terminal
            #
            else:
                a1=_RpTerminal(key,self.rp)
            definition.append([a1,mult,notrule])
        return definition
    def _interpretCode(self):
        """ interpret the code defined for rule 
          - variables defined in code must begin with '$'
            followed by the rule name
        """
        if len(self.code)==0: return
        sepcode=self.code[0]
        codes=self.code.split(sepcode)[1:]
        for cc in codes:
            #locate @xxxx  variable in code:
            # ex for code:    the_string="$char"+"---" 
            #  => group(1)='the_string="' 
            #  => group(2)='char'        ==> the variable that will be found in _VALS
            #  => group(3)='"+"---" '
            m=re.match(r'^([^\$]*)\$([A-Za-z0-9_]*)(.*)$',cc,re.DOTALL)   #0.91
            while m!=None:
                _deb=m.group(1)
                _var=m.group(2)
                _fin=m.group(3)
                if self.rp.vals.has_key(_var):
                    # Escape interpreted code as it will later cause trouble
                    escaped_val=self.rp.vals.get(_var).replace("\\t","t").replace("\\u","u")
                    cc=_deb+escaped_val+_fin
                else:
                    raise Exception,_var+' not set'
                m=re.match(r'^([^\$]*)\$([A-Za-z0-9_]*)(.*)$',cc,re.DOTALL)  #0.91
            if self.rp.execute_code:
                try:
                    exec(cc,self.rp.vals)
                except Exception,error:
                    print '+++',error
                    print '+++Code=',cc
            self.rp.code_array.append(cc)

class _RpTerminal:
    """ class to handle terminals """
    def __init__(self,term,rp):
        """ init terminal
          - check abbreviation of terminal 
            ex:  SEParator  
            minimum to check = 3
        """
        self.rp=rp
        term=term.strip()
        min=len(term)
        if term.isalnum():
            m=re.match(r'([A-Z0-9_]*)([a-z0-9_]*)',term)
            if m!=None:
                term=term.upper()
                min=len(m.group(1))
        self.terminal=term
        self.min=min
    def _parse(self,_tk,mult='',n_val=None):
        """ parse the terminal """
        if self.rp.verbose: print _tk.getIndent(True)+'Parsing terminal:"'+self.terminal+'" for string:"'+_tk.getRemaining()+'"'
        ret=-1
        _top=_tk.index
        _top2=_tk.removeBlanks()
        min=0
        while (min<self.min or min<len(self.terminal)) and _tk.peek().upper()==self.terminal[min]:
            _tk.read()
            min+=1
            ret=min
        if _tk.index - _top2 < self.min: 
            ret=-1
            _tk.reset(_top)
        if min>0 and min<len(self.terminal):
            ntok=_tk.peek().strip()
            nterm=self.terminal[min].strip()
            #print string.ascii_letters.find(ntok)
            # if next car of terminal diff of next car of token !!
            if ntok!='' and nterm!='' and string.ascii_letters.find(ntok)>-1 and ntok!=nterm:
                ret=-1
        if (mult=='?' or mult=='*'):
            ret=max(0,ret)
        _retstr=''
        _retindent='.'
        if ret>0: 
            _retstr=_tk.getString(_top2)
            _retindent='<'
        if self.rp.verbose: print _tk.getIndent(False,_retindent)+'Parsed terminal :"'+self.terminal+'" - value="'+_retstr+'"'
        return ret

class _RpRegular:
    """ class to handle regular expressions """
    def __init__(self,term,rp):
        """ init class, compile reg """
        self.source=term
        self.rp=rp
        self.regular=re.compile(term)
    def _parse(self,_tk,mult='',n_val=None):
        """ parsing string against reg expression """
        if self.rp.verbose: print _tk.getIndent(True)+'Parsing regular:"'+self.source+'" for string:"'+_tk.getRemaining()+'"'
        if n_val!=None and n_val==_tk.peek(): 
            if self.rp.verbose: print _tk.getIndent(False)+'Parsed regular :"'+self.source+'" - value=""'
            return -1
        ret=-1
        min=0
        _top=_tk.index
        if mult=='' or mult=='+':
            _passed=False
            try:
                _passed=self.regular.match(_tk.peek())
            except TypeError:
                pass
            if _passed:
                _tk.read()
                min+=1
                ret=min
                if mult=='+':
                    while 1:
                        try:
                            if self.regular.match(_tk.peek()):
                                min+=1
                                _tk.read()
                                ret=min
                            else:
                                break
                        except IndexError:
                            break
                
        elif mult=='?' or mult=='*':
            ret=0 # default for these mult
            if self.regular.match(_tk.peek()):
                _tk.read()
                min+=1
                ret=min
                if mult=='*':
                    while 1:
                        try:
                            if self.regular.match(_tk.peek()):
                                min+=1
                                _tk.read()
                                ret=min
                            else:
                                break
                        except IndexError:
                            break # end of string then return OK...
        else:
            raise Exception('Invalid multiplicator:',mult)
        if ret==-1:
            _tk.reset(_top)
        _retstr=''
        _retindent='.'
        if ret>0: 
            _retstr=_tk.getString(_top)
            _retindent='<'
        if self.rp.verbose: print _tk.getIndent(False,_retindent)+'Parsed regular :"'+self.source+'" - value="'+_retstr+'"'
        return ret
    
class RP:
    def __init__(self):
        self.rules={}           # Contain list of rules 
        self.vals={}            # Values of rules while parsing the string
        self.verbose=False      # Display rules in process...
        self.debug=False        # Debugging mode
        self.ignore_blanks=True # Default is: ignore blanks 
        self.execute_code=True  # Default is: execute code
        self.sepcode='@'
        self.code_array=[]
        self.code_init=[]
        self.code_post=[]
        self.code=''            #the code, user can run !
        self.maindef=None
        self.stringError=''
        self.rp_locals=locals
    def compile(self,rule):
        cmp1=re.compile(r'^\s*([A-Za-z0-9_-]*)\s*::=\s*([^'+self.sepcode+r']*)(.*)$') #  xxxx ::=yyyyyy @zzzzzz
        cmp2=re.compile(r'^\s*\|\s*([^'+self.sepcode+r']*)(.*)$')                   #       |  yyyyyy @zzzzzz
        cmp3=re.compile(r'^\s*'+self.sepcode+r'(.*)$')                              #                 @zzzzzz
        currentRule=None
        for line in rule:
            line=line.strip()
            if line=='' or line[0]=='#': continue
            else:
                m1,m2,m3,m4,m5,m6,m7=None,None,None,None,None,None,None
                m1=cmp1.match(line)
                if m1==None: m2=cmp2.match(line)
                if m2==None: m3=cmp3.match(line)
                if m3==None: m4=re.match(r'^\s*[Ii][Nn][Ii][Tt]\s+(.*)$',line)
                if m4==None: m5=re.match(r'^\s*[Ii][Mm][Pp][Oo][Rr][Tt]\s+(.*)$',line)
                if m5==None: m6=re.match(r'^\s*[Oo][Pp][Tt][Ii][Oo][Nn]\s+(.*)$',line)
                if m6==None: m7=re.match(r'^\s*[Pp][Oo][Ss][Tt]\s+(.*)$',line)
            if m1!=None:
                _rule=m1.group(1)
                if RESERVED.has_key(_rule):                                                         #0.91
                    raise Exception("Invalid rule name: '%s' is a python reserved word" % (_rule) ) #0.91
                _def=m1.group(2)
                _code=m1.group(3)
                if not self.rules.has_key(_rule):
                    currentRule=_RpRule(_rule,self)
                    self.rules[_rule]=currentRule
                else:
                    currentRule=self.rules[_rule]
                _def,newrules=splitBrackets(_def)
                _ndef=re.split(r'\|',_def) # split for | in def
                for _def in _ndef:
                    _def=_xlate(_def,True)
                    ruleDef=_RpDefinition(_def,self,_code)
                    currentRule.addDefinition(ruleDef)
                rule.extend(newrules)               
                if self.maindef==None: self.maindef=currentRule
            elif m2!=None:
                _def=m2.group(1)
                _code=m2.group(2)
                _def,newrules=splitBrackets(_def)
                _ndef=re.split(r'\|',_def) # split for | in def
                for _def in _ndef:
                    _def=_xlate(_def,True)
                    ruleDef=_RpDefinition(_def,self,_code)
                    currentRule.addDefinition(ruleDef)
                rule.extend(newrules)
            elif m3!=None:
                _code=m3.group(1)
                ruleDef._addcode(_code)
            elif m4!=None:
                _initcode=m4.group(1)
                self.code_init.append(_initcode)
            elif m5!=None:
                _infile=m5.group(1)
                try:
                    _file=open(_infile,'r')
                    _ret=_file.readlines()
                    _file.close()
                    rule.extend(_ret)
                except Exception:
                    raise Exception('File not found:'+_infile)
            elif m6!=None:
                val=m6.group(1).strip()
                uval=val.upper()
                if uval=='VERBOSE':
                    self.verbose=True
                elif uval=='TRACE':
                    self.trace=True
                elif uval=='BLANKS':
                    self.ignore_blanks=False
                elif uval=='NORUN':
                    self.execute_code=False
                elif len(val)>1:
                    vals=val.split(' ')
                    if vals[0].upper()=='SEPCODE':
                        self.sepcode=vals[1]
                        cmp1=re.compile(r'^\s*([A-Za-z0-9_-]*)\s*::=\s*([^'+self.sepcode+r']*)(.*)$') #  xxxx ::=yyyyyy @zzzzzz
                        cmp2=re.compile(r'^\s*\|\s*([^'+self.sepcode+r']*)(.*)$')                   #       |  yyyyyy @zzzzzz
                        cmp3=re.compile(r'^\s*'+self.sepcode+r'(.*)$')                              #                 @zzzzzz
                else:
                    raise Exception('Invalid option:'+val)
            elif m7!=None:
                _postcode=m7.group(1)
                self.code_post.append(_postcode)
                print "post:: "
                print self.code_post
            else:
                raise Exception('Invalid rule: '+line)
        self.check_rules()
        
    def check_rules(self):
        """ routine to check if all rules are defined """
        for k,v in self.rules.iteritems():
            if len(v.definitions)==0:
                raise Exception('No definition for rule:'+k)
            
    def match(self,data):
        if self.maindef.match(data):
            for x,y in self.vals.iteritems():
                if isinstance(y,str) and len(y)>0:
                    if y[0]=='"' or y[0]=="'":
                        exec("self."+x+"="+y)
                    else:
                        exec('self.'+x+'="""'+y+'"""')
                elif isinstance(y,int):
                    exec("self."+x+"="+str(y))
                elif isinstance(y,list):
                    exec("self."+x+"="+str(y))
            return self
        return None
        
    def get(self,var):
        if self.vals.has_key(var):
            return self.vals.get(var)
        return None
    
def _xlate(str,reverse=False):
    xlation={'"("':'"l_parent"',
             '")"':'"r_parent"',
             '"|"':'"or_term"',
             '"[':'"l_bracket"',
             ']"':'"r_bracket"'}
    for k,v in xlation.iteritems():
        if reverse:
            str=str.replace(v,k)
        else:
            str=str.replace(k,v)
    return str
    
def splitBrackets(inputStr):
    """ Split rules definitions 
        split along () , []
    """
    import random
    newrules=[]
    inputStr=_xlate(inputStr)
    # Now , split at (  )
    # ex:  r1 (r2) r3 (r4)* r5
    nr1=re.findall('\([^\)]*\)[\+\?\*]?',inputStr)  # => ['(r2)','(r4)*']
    nr2=re.split('\([^\)]*\)[\+\?\*]?',inputStr)    # => ['r1',r3','r5']
    nstr=nr2.pop(0) # => get 'r1'
    for nr in nr1:  # => get '(r2)' then '(r4)*' 
        if nr[-1]==')':
            suffix=''
            nr=nr[1:-1]
        else:
            suffix=nr[-1]
            nr=nr[1:-2]
        a_rule='rule' + str(random.randint(1,1000000))
        nstr+=(' '+a_rule+suffix+' ')
        newrules.append(a_rule+' ::= '+ _xlate(nr,True))
        nstr+=nr2.pop(0)    # => get 'r3' then 'r5'
    inputStr=nstr
    # Now , split at [ ]
    # ex:  r1 [r2] r3 [r4] r5
    nr1=re.findall('\[[^\]]*\]',inputStr)  # => ['[r2]','[r4]']
    nr2=re.split('\[[^\]]*\]',inputStr)    # => ['r1',r3','r5']
    nstr=nr2.pop(0) # => get 'r1'
    for nr in nr1:  # => get '[r2]' then '[r4]' 
        nr=nr[1:-1]
        a_rule='rule' + str(random.randint(1,1000000))
        nstr+=(' '+a_rule+'? ')
        newrules.append(a_rule+' ::= '+ _xlate(nr,True))
        nstr+=nr2.pop(0)    # => get 'r3' then 'r5'
    inputStr=nstr
    return inputStr,newrules
    

if __name__=='__main__':
    rule=['init loc_range=[] ',
          'locate    ::=   range?  string  ',
          'range     ::=   "(" group+ ")"                   ',
          '            |    group                            ',
          'group     ::=   grp          ',
          'grp       ::=   nn "-" mm    @loc_range.append([$nn,$mm])',
          '            |   nn "." mm    @loc_range.append([$nn,($nn+$mm)])',
          '            |   nn           @loc_range.append([$nn,9999])',
          'nn        ::=  r"[0-9]"+                              ',
          'mm        ::=  r"[0-9]"+                              ',
          'string    ::=  sep char* sep  @loc_string="$char" ',
          'sep       ::=  r"\S"  ',
          'char      ::=  r"." ^sep' ]
    stringsToTry=(' 1-20 /hello world/ ',
                  ' 4-10 ,12345678',
                  ' 4-10 ,aaaaaa,',
                  ' /location/',
                  ' (4.10 25-28 39.3) /location/ ',
                  ' (4.10 25-28  /location/   ',
                  ' 46-  /location/   ')    
    r=compile(rule)
    for st in stringsToTry:
        ok_ko=(r.match(st)!=None)
        print '\n---------', st, '------------',ok_ko
        if not ok_ko:
            print '"'+st+'"'
            print " "+r.stringError
        else:
            print "range=",r.loc_range
            print "string=",r.loc_string



        
