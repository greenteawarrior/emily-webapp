import os
import webapp2
import jinja2
from google.appengine.ext import db
import cgi
from string import ascii_lowercase
import re
import hashlib
import hmac
import urllib2
from xml.dom import minidom
import json
import logging
from google.appengine.api import memcache
import time
import unit4_functions as u4 #aka utils

jinja_environment = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 
           'templates')))

secret = "pewpewpew"

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

    def jsonrender(self, entrydict):
        json_text = json.dumps(entrydict)
        self.response.headers['Content-Type'] = 'application/json; charset = UTF-8'
        self.write(json_text)

    def escape_html(self,s):
        return cgi.escape(s, quote=True)

    def set_secure_cookie(self, name, cookie_val):
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        if cookie_val and u4.check_secure_val(cookie_val, secret):
            return cookie_val

    def login(self, username, secret):
        self.set_secure_cookie('username', u4.make_secure_val(username, secret))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'username=; Path=/')
        
    def which_format(self):
        if self.request.url.endswith('.json'):
            format = '.json'
        else:
            format = 'html'
        return format

    def wiki_base_links(self, currentlyediting=False):
        validate_username_cookie = self.read_secure_cookie('username')

        try: 
            username = validate_username_cookie.split("|")[0]
        except:
            username = None

        if username == None:
            pass
            link1_url = "/login"
            link1_label = "login"
            link2_url = "/signup"
            link2_label = "signup"

        elif u4.valid_username(username):
            if currentlyediting == True:
                link1_url = "/logout"
                link1_label = "logout"
                link2_url = ""
                link2_label = ""
            elif currentlyediting == False:
                link1_url = "/edit"
                link1_label = "edit"
                link2_url = "/logout"
                link2_label = "logout"

        return link1_url, link1_label, link2_url, link2_label


class User(db.Model):
    username = db.StringProperty(required = True)
    hashed_pw = db.StringProperty(required = True)
    email = db.StringProperty()

class Signup(Handler):
    def write_form(self, errors, username="", 
                         password="", 
                         verify="", 
                         email=""):
        username_error = errors[0] 
        password_error = errors[1] 
        verify_error = errors[2] 
        email_error = errors[3] 
        self.render('wiki_signup.html', {"username":username,
                                        "password":password,
                                        "verify": verify,
                                        "email": email,
                                        "username_error": username_error, 
                                        "password_error": password_error, 
                                        "verify_error": verify_error, 
                                        "email_error": email_error})
    

    def get(self):
        #Maybe add an error - if you're already logged in, 
        #raise an error message and ask the user if s/he 
        #would like to logout before proceeding.
        self.write_form(["", "", "", ""])

    def post(self):
        input_username = self.request.get("username")
        input_password = self.request.get("password")
        input_verify = self.request.get("verify")
        input_email = self.request.get("email")

        valid_username = u4.valid_username(input_username)
        valid_password = u4.valid_password(input_password)
        valid_verify = u4.valid_verify(input_password, input_verify)
        valid_email =  u4.valid_email(input_email)

        errors = ["", "", "", ""]

        if not valid_username:
            errors[0] = "That's not a valid username."
        if not valid_password:
            errors[1] = "That wasn't a valid password."
        if not valid_verify:
            errors[2] = "Your passwords didn't match."
        if not valid_email and input_email != "":
            errors[3] = "That's not a valid email."
        
        if errors != ["", "", "", ""]:
            self.write_form(errors, input_username, "", "", input_email)
        else:  
            user_existence = User.all().filter('username =', input_username).get()
            if user_existence:
                errors[0] = "That user already exists."
                self.write_form(errors, input_username, "", "", input_email)
            else:
                hashed_pw = u4.make_pw_hash(str(input_username), str(input_password))
                u= User(username=str(input_username), hashed_pw=hashed_pw, email=str(input_email))
                u.put()
                self.login(username=str(input_username), secret=secret)
                self.redirect("/welcome")

class UserWelcome(Handler):
    def get(self):
        validate_username_cookie = self.read_secure_cookie('username')
        try: 
            username = validate_username_cookie.split("|")[0]
            if u4.valid_username(username):
                self.render('wiki_welcome.html', {"username":username})
        except:
            self.redirect("/signup")

class Login(Handler):
    def write_form(self, loginerror="", username="", password=""):
        self.render('wiki_login.html', {"username":username,
                                        "password":password,
                                        "loginerror":loginerror})

    def get(self):
        self.write_form()

    def post(self):
        login_input_username = self.request.get("username")
        login_input_pw = self.request.get("password")

        u = User.all().filter('username =', login_input_username).get()
        if u: 
            hashed_pw = u.hashed_pw
            if u4.valid_pw(login_input_username, login_input_pw, hashed_pw):
                self.login(username=str(login_input_username), secret=secret)
                self.redirect("/welcome")
            else:
                loginerror = "Invalid username and password combination."
                self.write_form(loginerror=loginerror, username=login_input_username)
        else:
            loginerror = "Username does not exist in database."
            self.write_form(loginerror=loginerror)

class Logout(Handler):
    def get(self):
        self.logout()
        self.redirect('/login')

class Page(db.Model):
    "Database entity: wiki pages written and submitted by users."
    name = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

    def entry_dict(self):
        #this dictionary will be converted into JSON
        time_fmt = '%c'
        d = {'content': self.content,
             'created': self.created.strftime(time_fmt)}
        return d


class EditPage(Handler):
    def render_pageform(self, links, content="", error=""):
        self.render("wiki_pageform.html", {"content":content, 
                                           "error":error,
                                           "link1_url":links[0],
                                           "link1_label":links[1],
                                           "link2_url":links[2],
                                           "link2_label":links[3]
                                           })

    def get(self, pagename):
        links = self.wiki_base_links(currentlyediting=True)
        if links[1] == "login":
            self.render("wiki_permission.html", {"link1_url":links[0],
                                                 "link1_label":links[1],
                                                 "link2_url":links[2],
                                                 "link2_label":links[3]
                                                })
        else:
            page = get_page_from_cache(pagename)
            try:
                pagecontent = page.content
            except:
                pagecontent=""
            self.render_pageform(content=pagecontent, links=linkslist)

    def post(self, pagename):
        content_input = self.request.get("content")
        if pagename and content_input:
            p = Page(name = pagename, content=content_input)
            p.put()
            time.sleep(.1) #to account for delay between database put and memcache, apparently an ancestor query will also solve this delay problem
            p_id = p.key().id()
            memcache.delete(pagename)
            self.redirect(pagename)
        else:
            error = "This page is hungry for content!"
            self.render_pageform(content, error)

def get_page_from_cache(pagename):
    key = str(pagename)

    page_contents = memcache.get(key)
    #If statement is bypassed if the page contents are 
    #already in memcache
    if page_contents is None:
        #for the "Queried X seconds ago" feature
        page_query_time = time.time()
        memcache.set(key+" query_time", page_query_time)
        logging.error(key+" QUERY (WIKI PAGE)")
        
        #Database query
        q = Page.all()
        q.filter("name =", key).order('-created')
        page_contents = q.get()
        
        #Storing the page contents in memcache
        memcache.set(key, page_contents)
    return page_contents

class WikiPage(Handler):
    #future work- json compatibility code in the get function
    def get(self, pagename):
        links = self.wiki_base_links()
        page = get_page_from_cache(pagename)
        query_time = memcache.get(pagename+" query_time")
        if query_time == None:
            query_time = 0
        page_query_sec_ago = time.time() - query_time
        if not page:
            self.redirect("/_edit"+pagename)
        self.render("wiki_page.html", {"page":page, 
                                       "page_query_sec_ago":page_query_sec_ago,
                                        "link1_url":links[0],
                                        "link1_label":links[1],
                                        "link2_url":links[2],
                                        "link2_label":links[3]
                                       })

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'

app = webapp2.WSGIApplication([('/signup', Signup),
                               ('/welcome', UserWelcome),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/_edit' + PAGE_RE, EditPage),
                               (PAGE_RE, WikiPage),
                               ],
                              debug=True)
