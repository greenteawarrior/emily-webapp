import webapp2
import cgi
import re

form = """ 
<form method = "post"> 
    <h2>Signup</h2>
    <br>
    <label> Username
        <input type="text" name="username" value="%(username)s">
    </label>
    <div style="color: red">%(username_error)s</div>
    <br>
    <label> Password
        <input type="password" name="password" value="%(password)s">
    </label>
    <div style="color: red">%(password_error)s</div>    
    <br>
    <label> Verify Password
        <input type="password" name="verify" value="%(verify)s">
    </label>
    <div style="color: red">%(verify_error)s</div>    
    <br>
    <label> Email (optional)
        <input type="text" name="email" value="%(email)s">
    </label>    
    <div style="color: red">%(email_error)s</div>
    <br>
    <br>
    <input type = "submit">
</form>
""" 

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return USER_RE.match(username)

PASSWORD_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return PASSWORD_RE.match(password)

def valid_verify(password, verify):
    if password == verify:
        return True
    else:
        return None

EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
def valid_email(email):
    return EMAIL_RE.match(email)

def escape_html(s):
    return cgi.escape(s, quote=True)

class UserSignUp(webapp2.RequestHandler):
    def write_form(self, errors, username="", 
                         password="", 
                         verify="", 
                         email=""):
        username_error = errors[0] 
        password_error = errors[1] 
        verify_error = errors[2] 
        email_error = errors[3] 
        self.response.out.write(form % {"username":username,
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

        username = valid_username(input_username)
        password = valid_password(input_password)
        verify = valid_verify(input_password, input_verify)
        email =  valid_email(input_email)

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
            self.redirect("/thanks?username=" + input_username)            

class ThanksHandler(UserSignUp): 
    def get(self):
        username = self.request.get("username")
        if valid_username(username):
            self.response.out.write("Welcome, %s!" % username)
        else:
            self.redirect("/user-signup")

app = webapp2.WSGIApplication([('/user-signup', UserSignUp), ('/thanks', ThanksHandler)], debug=True)
