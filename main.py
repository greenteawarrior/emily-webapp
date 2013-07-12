import os
import webapp2
import jinja2
from google.appengine.ext import db
import cgi
from string import ascii_lowercase
import re
import hashlib
import hmac

pages = []

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

    def escape_html(self,s):
        return cgi.escape(s, quote=True)

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


# usersignup, pset2 and 4
class UserSignUp(Handler):
    def valid_username(self, username):
        USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
        return USER_RE.match(username)

    def valid_password(self, password):
        PASSWORD_RE = re.compile(r"^.{3,20}$")
        return PASSWORD_RE.match(password)

    def valid_verify(self, password, verify):
        if password == verify:
            return True
        else:
            return None

    def valid_email(self, email):
        EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
        return EMAIL_RE.match(email)

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
        self.write_form(["", "", "", ""])

    def post(self):
        input_username = self.request.get("username")
        input_password = self.request.get("password")
        input_verify = self.request.get("verify")
        input_email = self.request.get("email")

        username = self.valid_username(input_username)
        password = self.valid_password(input_password)
        verify = self.valid_verify(input_password, input_verify)
        email =  self.valid_email(input_email)

        errors = ["", "", "", ""]

        if not username:
            errors[0] = "That's not a valid username."
        if not password:
            errors[1] = "That wasn't a valid password."
        if not verify:
            errors[2] = "Your passwords didn't match."
        if not email and input_email != "":
            errors[3] = "That's not a valid email."
        
        if errors != ["", "", "", ""]:
            self.write_form(errors, input_username, "", "", input_email)
        else:  
            self.redirect("/usersignup/welcome?username=" + input_username) 
pages.append(('/usersignup', UserSignUp))

class UserWelcome(Handler): 
    def valid_username(self, username):
        USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
        return USER_RE.match(username)

    def get(self):
        username = self.request.get("username")
        if self.valid_username(username):
            self.write("Welcome, %s!" % username)
        else:
            self.redirect("/user-signup")
pages.append(('/usersignup/welcome', UserWelcome))


class Art(db.Model):
    "Database entity: the ascii art submission from the user."
    title = db.StringProperty(required = True)
    art = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)


class AsciiMainPage(Handler):
    def render_front(self, title="", art="", error=""):
        arts = db.GqlQuery("SELECT * FROM Art "
                           "ORDER BY created DESC ") #run a query
        self.render("front.html", {"title":title, 
                                   "art": art, 
                                   "error":error, 
                                   "arts":arts})

    def get(self):
        self.render_front()

    def post(self):
        title = self.request.get("title")
        art = self.request.get("art")
        if title and art:
            a = Art(title=title, art=art)
            a.put()
            self.redirect("/")
        else:
            error = "We need both a title and some artwork!"
            self.render_front(title, art, error)
pages.append(('/asciichan', AsciiMainPage))


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
pages.append(('/blog', BlogMainPage))


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
pages.append(('/blog/newpost', BlogNewEntry))


class IndividualEntry(Handler):
    def get(self, e_id):
        entry = BlogEntry.get_by_id(int(e_id))
        self.render("blogindividualentry.html", {"entry":entry})
pages.append(('/blog/(\d+)', IndividualEntry))

class CookieVisitPage(Handler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        visits = 0
        visit_cookie_str = self.request.cookies.get('visits')
        if visit_cookie_str:
            cookie_val = check_secure_val(visit_cookie_str)
            if cookie_val:
                visits = int(cookie_val)
        visits += 1
        new_cookie_val = make_secure_val(str(visits))
        self.response.headers.add_header('Set-Cookie', 'visits=%s' % new_cookie_val)
        if visits > 10000:
            self.write("You are the best ever!")
        else:
            self.write("You've been here %s times!" % visits)
pages.append(('/cookies', CookieVisitPage))

app = webapp2.WSGIApplication(pages, debug=True)
