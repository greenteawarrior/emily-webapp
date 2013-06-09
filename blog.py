import os
import webapp2
import jinja2

from google.appengine.ext import db

jinja_environment = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 
           'templates')))

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

class BlogEntry(db.Model):
    "Database entity: blog posts written and submitted by users."
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

class BlogMainPage(Handler):
    def render_blogfront(self):
        entries = db.GqlQuery("SELECT * FROM BlogEntry ORDER BY created DESC")
        self.render('blogfront.html', {'entries':entries})
    
    def get(self):
        self.render_blogfront()

class BlogNewEntry(Handler):
    def render_blogform(self, subject="", content="", error=""):
        self.render("blogform.html", {"subjectstr":subject, 
                                      "contentstr":content, 
                                      "error":error})

    def get(self):
        self.render_blogform()

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")
        if subject and content:
            e = BlogEntry(subject=subject, content=content)
            e.put()
            e_id = e.key().id()
            self.redirect("/blog/"+str(e_id), e_id)
        else:
            error = "We need both a subject and content!"
            self.render_blogform(subject, content, error)

class IndividualEntry(Handler):
    def get(self, e_id):
        entry = BlogEntry.get_by_id(int(e_id))
        self.render("blogindividualentry.html", {"entry":entry})

app = webapp2.WSGIApplication([('/blog', BlogMainPage), 
                               ('/blog/newpost', BlogNewEntry), 
                               ('/blog/(\d+)', IndividualEntry)], 
                               debug=True)
