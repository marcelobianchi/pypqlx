from __future__ import print_function, division

from twisted.web.server import Site
from twisted.web.resource import Resource, NoResource
from twisted.internet import reactor, endpoints
from twisted.web.static import File

##
# HTML helper methods
##
SITEBASE = 'web'

def page(pagetitle, content):
    global SITEBASE
    msg = '''
<!DOCTYPE html>

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
            li(a('application.wadl', '/application.wadl') + ': The Query method is the one that you should use to get data.'),
            li(a('query', '/query') + ': The Query method is the one that you should use to get data.'),
        ]
        msg += title('Available Resources are:', 2)
        msg += ol(lis)
        
        return page('Help Page', msg)

class pq_query(Resource):
    isLeaf = True

    def render_GET(self, request):
        return ""

class PQLXWebServer(Resource):
    def getChild(self, name, request):
        if name == "query":
            return pq_query()
        
        if name == "application.wadl":
            return File("{}/application.wadl".format(SITEBASE), defaultType='application/xml')
        
        if name == "":
            return pq_help()
        return NoResource()

##
# Main Reactor
##

if __name__ == "__main__":
    root = PQLXWebServer()
    root.putChild(SITEBASE, File("{}/".format(SITEBASE)))
    
    factory = Site(root)
    endpoint = endpoints.TCP4ServerEndpoint(reactor, 8080)
    endpoint.listen(factory)
    reactor.run()
