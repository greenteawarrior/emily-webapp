import os
import webapp2
import jinja2

from google.appengine.ext import db

#importing the different webpages from the class lessons/exercises
import hello-udacity
import birthday
import jingatime
import rot13
import user-signup
import asciichan

pagelist = []

jinja_environment = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

class Handler(webapp2.RequestHandler):
    def write(self, writeme):
        """Shorthand for self.response.out.write."""
        self.response.out.write(writeme)

    def render(self, template, paramdict):
        """
        Helper function for rendering.
        Arguments: self, template, paramdict
        self is self
        template is a .html, should be located in templates directory
        paramdict is a dictionary where keys are the template variables 
                  and values are the desired values for corresponding variables
        """
        t = jinja_environment.get_template(template)
        self.response.out.write(t.render(paramdict))

app = webapp2.WSGIApplication([('/', MainPage)], debug=True)
