import os
import webapp2
import jinja2
from google.appengine.ext import db
import cgi
from string import ascii_lowercase
import re
import hashlib
import hmac
import unit4_functions as u4
import urllib2
from xml.dom import minidom
import json
import logging
from google.appengine.api import memcache
import time

pages = []

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

class HelloPage(Handler):
    def get(self):
        self.write("Hello, Udacity!")
pages.append(('/helloudacity', HelloPage))


class JingaPage(Handler):
    def get(self):
        template_values = {'name': 'SomeGuy', 'verb': 'extremely enjoy'}
        self.render('jingatest.html', template_values)
pages.append(('/jingatime', JingaPage))


class BirthdayPage(Handler):
    def valid_month(self, month):
        months = ['January',
                  'February',
                  'March',
                  'April',
                  'May',
                  'June',
                  'July',
                  'August',
                  'September',
                  'October',
                  'November',
                  'December']  
        month_abbs = dict((m[:3].lower(), m) for m in months)
        if month:
            short_month = month[:3].lower()
            return month_abbs.get(short_month)
        else:
            return None

    def valid_day(self, day):
        if day and day.isdigit():
            day = int(day)
            if day > 0 and day <= 31:
                return day
        else:
            return None

    def valid_year(self, year):
        if year and year.isdigit():
            year = int(year)
            if year >= 1900 and year <= 2020:
                return year
        else:
            return None
    
    def write_form(self, error="", month="", day="", year=""):
        bdayparamdict = {"error": error,
                     "month": self.escape_html(month),
                     "day": self.escape_html(day),
                     "year": self.escape_html(year)}
        self.render("bdayform.html", bdayparamdict)             

    def get(self):
        self.write_form()

    def post(self):
        user_month = self.request.get('month')
        user_day = self.request.get('day')
        user_year = self.request.get('year')

        month = self.valid_month(user_month)
        day = self.valid_day(user_day)
        year = self.valid_year(user_year)

        if not (month and day and year):
            self.write_form("That doesn't look valid to me, friend.", 
                            user_month, user_day, user_year)
        else:
            self.redirect("/birthday/thanks")
pages.append(('/birthday', BirthdayPage))

class BirthdayThanks(Handler):
    def get(self):
        self.write("Thanks! That's a totally valid day. ^w^")
pages.append(('/birthday/thanks', BirthdayThanks))


class rot13Page(Handler):
    def write_form(self, formtext=""):
        r13paramdict = {"formtext": formtext}
        self.render('r13form.html', r13paramdict)

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
        return self.escape_html(res)

    def get(self):
        self.write_form()

    def post(self):
        formtext = self.request.get("text")
        rot13text = self.rot13(formtext)
        self.write_form(rot13text)        
pages.append(('/rot13', rot13Page))


class Art(db.Model):
    "Database entity: the ascii art submission from the user."
    title = db.StringProperty(required = True)
    art = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    coords = db.GeoPtProperty()

IP_URL = "http://api.hostip.info/?ip="

def get_coordinates(ip):
    #ip = "4.2.2.2" #this is a name server that helps resolve DNS names into IP's
    url = IP_URL + ip
    content = None
    try:
        content = urllib2.urlopen(url).read()
    except URLError:
        return

    if content:
        #parse the XML and find the coordinates
        x = minidom.parseString(content)
        coords_in_xml= x.getElementsByTagName("gml:coordinates")
        if coords_in_xml and coords_in_xml[0].childNodes[0].nodeValue:
            coordslist = coords_in_xml[0].childNodes[0].nodeValue.split(',')
            lon = coordslist[0]
            lat = coordslist[1]
            return db.GeoPt(lat, lon) #google app engine datatype for locations        


def gmaps_img(points):
    GMAPS_URL = "http://maps.googleapis.com/maps/api/staticmap?size=380x263&sensor=false&"
    markerstr = ""
    for p in points:
        markerstr += "markers=%s,%s&" % (p.lat, p.lon)
    markerstr = markerstr[:-1] #get rid of the very last ampersand
    return GMAPS_URL + markerstr

def top_arts(update = False):
    key = 'top'
    arts = memcache.get(key)
    if arts is None or update:
        logging.error("DB QUERY")
        arts = db.GqlQuery("SELECT * FROM Art "
                           "ORDER BY created DESC LIMIT 10 ") #run a query
        #prevent the running of multiple queries
        arts = list(arts)
        memcache.set(key, arts)
    return arts
 

class AsciiMainPage(Handler):
    def render_front(self, title="", art="", error=""):
        arts = top_arts()

        # find which arts have coords
        coordpoints  = []
        for a in arts:
            if a.coords:
                coordpoints.append(a.coords)
        # also same code but more succinct: points = filter(None, (a.coords for a in arts))
        
        # if we have any arts coords, make an image url
        img_url = None
        if coordpoints:
            img_url = gmaps_img(coordpoints)

        self.render("front.html", {"title":title, 
                                   "art": art, 
                                   "error":error, 
                                   "arts":arts,
                                   "img_url":img_url})


    def get(self):
        # debugging location functionality
        # self.write(self.request.remote_addr)
        # self.write(repr(get_coordinates(self.request.remote_addr)))
        self.render_front()

    def post(self):
        title = self. request.get("title")
        art = self.request.get("art")
        if title and art:
            a = Art(title=title, art=art)
            #look up the user's coordinates from their IP
            coords = get_coordinates(self.request.remote_addr)
            #if we have coordinates, add them to the Art
            if coords:
                a.coords = coords
            a.put()
            #rerun the query and update the cache
            #prevents cache stampedes
            top_arts(True)
            #and thus, a pageview will not hit the database :]
            self.redirect("/asciichan")
        else:
            error = "We need both a title and some artwork!"
            self.render_front(title, art, error)
pages.append(('/asciichan', AsciiMainPage))


# usersignup, pset2 and 4
class User(db.Model):
    username = db.StringProperty(required = True)
    hashed_pw = db.StringProperty(required = True)
    email = db.StringProperty()

class UserSignUp(Handler):
    def write_form(self, errors, username="", 
                         password="", 
                         verify="", 
                         email=""):
        username_error = errors[0] 
        password_error = errors[1] 
        verify_error = errors[2] 
        email_error = errors[3] 
        self.render('usersignupform.html', {"username":username,
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
            #pset 2 style
            #self.redirect("/usersignup/welcome_pset2style?username=" + input_username) 

            #pset 4 style
            user_existence = User.all().filter('username =', input_username).get()
            if user_existence:
                errors[0] = "That user already exists."
                self.write_form(errors, input_username, "", "", input_email)
            else:
                hashed_pw = u4.make_pw_hash(str(input_username), str(input_password))
                u= User(username=str(input_username), hashed_pw=hashed_pw, email=str(input_email))
                u.put()
                self.login(username=str(input_username), secret=secret)
                self.redirect("/blog/welcome")

pages.append(('/blog/signup', UserSignUp))

class UserWelcome_pset2style(Handler): 
    def get(self): 
        username = self.request.get("username")
        if u4.valid_username(username):
            self.write("Welcome, %s!" % username)
        else:
            self.redirect("/blog/signup")
pages.append(('/blog/signup/welcome_pset2style', UserWelcome_pset2style))

class UserWelcome_pset4style(Handler):
    def get(self):
        validate_username_cookie = self.read_secure_cookie('username')
        username = validate_username_cookie.split("|")[0]
        if u4.valid_username(username):
            self.write("Welcome, %s!" % username)
        else:
            self.redirect("/blog/signup")
pages.append(('/blog/welcome', UserWelcome_pset4style))

class UserLogin(Handler):
    def write_form(self, loginerror="", username="", password=""):
        self.render('bloglogin.html', {"username":username,
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
                self.redirect("/blog/welcome")
            else:
                loginerror = "Invalid username and password combination."
                self.write_form(loginerror=loginerror, username=login_input_username)
        else:
            loginerror = "Username does not exist in database."
            self.write_form(loginerror=loginerror)
pages.append(('/blog/login', UserLogin))

class UserLogout(Handler):
    def get(self):
        self.logout()
        self.redirect('/blog/signup')
pages.append(('/blog/logout', UserLogout))

class BlogEntry(db.Model):
    "Database entity: blog posts written and submitted by users."
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

    def entry_dict(self):
        #this dictionary will be converted into JSON
        time_fmt = '%c'
        d = {'subject': self.subject,
             'content': self.content,
             'created': self.created.strftime(time_fmt)}
        return d

def home_blogposts(update=False):
    key = 'blog-home'
    entries = memcache.get(key)
    blog_query_time = memcache.get('most_recent_query_time')
    if entries is None or update:
        blog_query_time = time.time()
        memcache.set('most_recent_query_time', blog_query_time)
        logging.error("BLOG DB QUERY")
        entries = db.GqlQuery("SELECT * FROM BlogEntry ORDER BY created DESC")
        entries = list(entries)
        memcache.set(key, entries)
    return entries

class BlogMainPage(Handler):
    def render_blogfront(self):
        entries = home_blogposts()
        blog_query_time = memcache.get('most_recent_query_time')
        if blog_query_time == None:
            blog_query_time = 0
        query_sec_ago = time.time()-blog_query_time
        if self.which_format() == 'html':
            self.render('blogfront.html', {'entries':entries, 'query_sec_ago':query_sec_ago})
        elif self.which_format() == '.json':
            return self.jsonrender([e.entry_dict() for e in entries])

    def get(self):
        self.render_blogfront()
pages.append(('/blog/?(?:\.json)?', BlogMainPage))

class BlogNewEntry(BlogMainPage):
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
            time.sleep(.1) #to account for delay between database put and memcache, apparently an ancestor query will also solve this delay problem
            home_blogposts(update=True)
            e_id = e.key().id()
            self.redirect("/blog/"+str(e_id), e_id)
        else:
            error = "We need both a subject and content!"
            self.render_blogform(subject, content, error)
pages.append(('/blog/newpost', BlogNewEntry))


class IndividualEntry(Handler):
    def get(self, e_id):
        entry = BlogEntry.get_by_id(int(e_id))
        if not entry:
            self.error(404)
            return
        if self.which_format() == 'html':
            self.render("blogindividualentry.html", {"entry":entry})
        elif self.which_format() == '.json':
            self.jsonrender(entry.entry_dict())
pages.append(('/blog/(\d+)(?:\.json)?', IndividualEntry))


class CookieVisitPage(Handler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        visits = 0
        visit_cookie_str = self.request.cookies.get('visits')
        if visit_cookie_str:
            cookie_val = u4.check_secure_val(visit_cookie_str, secret)
            if cookie_val:
                visits = int(cookie_val)
        visits += 1
        new_cookie_val = u4.make_secure_val(str(visits), secret)
        self.response.headers.add_header('Set-Cookie', 'visits=%s' % new_cookie_val)
        if visits > 10000:
            self.write("You are the best ever!")
        else:
            self.write("You've been here %s times!" % visits)
pages.append(('/cookies/?', CookieVisitPage))

app = webapp2.WSGIApplication(pages, debug=True)