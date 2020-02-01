#!/usr/bin/python3

from __future__ import print_function, division

import sys, json

from twisted.web.server import Site
from twisted.web.resource import Resource, NoResource
from twisted.internet import reactor, endpoints
from twisted.web.static import File

from pypqlx import pdate, ptime, PQLXdb, get_nhnm, get_nlnm, E
import numpy as np 

##
# HTML helper methods
##
SITEBASE = 'web'

def page(pagetitle, content):
    global SITEBASE
    
    msg = '''<!DOCTYPE html>

<html>
<head>
    <meta charset="UTF-8">
    <title>{}</title>
    <link rel="stylesheet" href="{}/base.css">
</head>

<body>
{}
</body>

</html>
'''
    return msg.format(pagetitle, SITEBASE, content)

def title(content, level = 1):
    return '<h{}>{}</h{}>\n\n'.format(level, content,level)

def p(content):
    return "<p>{}</p>\n\n".format(content)

def li(content):
    return "<li>{}</li>".format(content)

def ol(lis):
    return "<ul>{}</ul>".format("\n".join(lis))

def ul(lis):
    return "<ul>{}</ul>".format("\n".join(lis))

def a(content, target):
    return '<a href="{}">{}</a>'.format(target, content)

##
# Server Resources
##

class pq_help(Resource):
    isLeaf = True
    
    def render_GET(self, request):
        msg = title('PQLX WebServer Help Page')
        msg += p('This is pqlx system @ localhost serving PDFs & more!')
        lis = [
            li(a('query', '/query') + ': The Query method is the one that you should use to get data.'),
            li(a('application.wadl', '/application.wadl') + ': The Query method is the one that you should use to get data.'),
            li(a('Test Web Page', '/web/test.html') + ': This is a web test page for the system.'),
        ]
        msg += title('Available Resources are:', 2)
        msg += ol(lis)
        
        return page('Help Page', msg).encode('utf-8')

class pq_query(Resource):
    isLeaf = True
    
    def __init__(self, db):
            Resource.__init__(self)
            self.db = db
    
    def __parseargs__(self, args):
        def pquantity(v):
            v = v.split(",")
            qq = []
            for q in v:
                if q not in ['mean', 'median', 'mode', 'min', 'max']: raise ValueError("Invalid quantity value.")
                qq.append(q)
            return set(qq)
        def pbool(v): return True if v in [ "true", "1", 1 ] else False
        def ploc(v) : return ("--" if str(v) == "" else str(v))
        def pdow(v):
            valid = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']
            v = v.split(",")
            if len(v) == 0: raise ValueError("Week days cannot be empty.")
            for iv in v:
                if iv not in valid: raise ValueError("Value: {} is invalid".format(iv))
            return v
        
        validargs = [ 'net', 'sta', 'loc', 'cha', 'starttime',
                      'endtime', 'nsegments', 'quantity', 'minhour',
                      'maxhour', 'dow', 'includemodels', 'includestd' ]
        
        parser    = dict(zip(validargs, [ str, str, ploc, str, pdate,
                      pdate, int, pquantity, ptime,
                      ptime, pdow, pbool, pbool]))
        
        defaults  = dict(zip(validargs, [ None, None, "--", None, None,
                      None, 1, [ 'mean' ], False,
                      False, False, False, False]))
        
        needed    = { 'net', 'sta', 'cha', 'starttime', 'endtime' }
        
        first = lambda x: str(x[0].decode('utf-8')).strip('"').strip("'")
        
        collectedargs = { }
        
        for barg in args:
            arg = barg.decode('utf-8')
            
            if arg not in validargs: raise ValueError("Bad parameter {} in query.".format(arg))
            if arg in needed: needed.remove(arg)
            
            try:
                value = first(args[barg])
                collectedargs[arg] = parser[arg](value)
            except Exception:
                raise ValueError("Cannot parse parameter {}={}.".format(arg, args[barg][0]))
        
        if len(needed) != 0:
            raise ValueError("Missing parameters in query {}.".format(",".join(needed)))
        
        for arg in validargs:
            if arg not in collectedargs:
                collectedargs[arg] = defaults[arg]
        
        return collectedargs
    
    def __models__(self, yes, periods = None):
        if yes is False or None: return None
        
        hper, hmodel = get_nhnm(periods)
        lper, lmodel = get_nlnm(periods)
        
        if not np.all(lper == hper):
            lmodel = np.inter(hper, lper, lmodel)
        
        model = {
            'periods' : list(hper),
            'nhnm'    : list(hmodel),
            'nlnm'    : list(lmodel),
        }
        
        return model
    
    def render_GET(self, request):
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Methods', 'GET')
        request.setHeader('Access-Control-Allow-Headers', 'x-prototype-version,x-requested-with')
        
        try:
            args = self.__parseargs__(request.args)
        except ValueError as e:
            request.setResponseCode(400)
            return str(e).encode('utf-8')
        
        try:
            pdfs = self.db.N_PDF(args['starttime'], args['endtime'],
                                args['net'], args['sta'], args['cha'], args['loc'],
                                NS = args['nsegments'])
            
            if len(pdfs) == 0:
                request.setResponseCode(204)
                return "".encode('utf-8')
            
            result = {
                'pdfs'    : list(map(lambda x: x.DICT(args['quantity'], True, args['includestd']), pdfs)),
                'models'  : self.__models__(args['includemodels'], pdfs[0].period)
            }
        except E as e:
            request.setResponseCode(400)
            return str(e).encode('utf-8')
                
        return json.dumps(result, indent = 2).encode('utf-8')

class PQLXWebServer(Resource):
    def __init__(self, db):
            Resource.__init__(self)
            self.db = db
    
    def getChild(self, name, request):
        name = name.decode('utf-8')
        if name == "query":
            return pq_query(self.db)
        
        if name == "application.wadl":
            return File("{}/application.wadl".format(SITEBASE), defaultType='application/xml')
        
        if name == "":
            return pq_help()

        return NoResource()

##
# Main Reactor
##

if __name__ == "__main__":
    print("Loading database ... ", file = sys.stderr)
    db = PQLXdb(user=sys.argv[1],
            password=sys.argv[2],
            machine=sys.argv[3],
            basedb=sys.argv[4])
    print("Database is UP!", file = sys.stderr)
    
    root = PQLXWebServer(db)
    root.putChild(SITEBASE.encode('utf-8'), File("{}/".format(SITEBASE)))
    
    factory = Site(root)
    endpoint = endpoints.TCP4ServerEndpoint(reactor, 8080)
    endpoint.listen(factory)
    reactor.run()
    
    db.close()

