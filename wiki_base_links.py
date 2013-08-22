# validate_username_cookie = self.read_secure_cookie('username')
#     try: 
#         username = validate_username_cookie.split("|")[0]
#         if u4.valid_username(username):
#             self.render('wiki_welcome.html', {"username":username})
#     except:
#         self.redirect("/signup")


def wiki_base_links(self):
    validate_username_cookie = self.read_secure_cookie('username')
    link1 = ""
    link2 = ""

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
