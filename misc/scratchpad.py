HTTP request (request line)
GET /foo HTTP/11.

HTTP response 
HTTP/1.1 200 OK


# GET request : parameter in URL, 
                # used for fetching documents (what page you're on, what you're searching for), 
                # have a maximum URL length, 
                # OK to cache, 
                # shouldn't change the server

# POST request :   parameter in request body, 
                 # used for updating data, 
                 # no max length, 
                 # not OK to cache, 
                 # OK to change the server (should be updating the server)

# HTML escaping:
# 	" --> &quot;
# 	> --> &gt;
# 	< --> &lt;
# 	& --> &amp;
	
def escape_html(s):
    res = ''
    for c in s:
        if c == "&":
        	res += "&amp;"
        elif c == ">":
            res += "&gt;"
        elif c == "<":
            res += "&lt;"
        elif c == '"':
            res += "&quot;"
        else: 
            res += c
    return res

def escape_html(s):
	for (i,o) in (("&", "&amp;"), 
				  (">", "&gt;"), 
				  ("<", "&lt;"), 
				  ('"', "&quot;")):
		s = s.replace(i,o)
	return s

import cgi
