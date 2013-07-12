import webapp2
import cgi
from string import ascii_lowercase

form = """ 
<form method = "post"> 
    <h1>Enter some text to ROT13:
    <br>
    <input type="textarea" name="text" value="%(formtext)s">
    <br>
    <input type = "submit">
</form>
""" 

def escape_html(s):
    return cgi.escape(s, quote=True)

class rot13(webapp2.RequestHandler):
    def write_form(self, formtext=""):
        self.response.out.write(form % {"formtext":formtext})

    def rot13(self, formtext):
        lowercases = list(ascii_lowercase)
        uppercases = [i.upper() for i in lowercases]
        res = ""
        for c in formtext:
            if c in lowercases:
                cindex = lowercases.index(c)
                if cindex < 13:
                    res += lowercases[cindex+13]
                else:
                    res += lowercases[cindex+13-26]
            elif c in uppercases:
                cindex = uppercases.index(c)
                if cindex < 13:
                    res += uppercases[cindex+13]
                else:
                    res += uppercases[cindex+13-26]                
            else:
                res += c
        return escape_html(res)

    def get(self):
        self.write_form()

    def post(self):
        formtext = self.request.get("text")
        rot13text = self.rot13(formtext)
        self.write_form(rot13text)

app = webapp2.WSGIApplication([('/rot13', rot13)], debug=True)