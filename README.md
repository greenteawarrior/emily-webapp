emily-webapp
============

[udacity web development] webdev exercises and blog project 

built with the python SDK for google app engine!

	Currently, you can view the wiki project at http://emily-webapp.appspot.com

wiki.py is the file for the wiki project. wiki.py is completely separate from main.py; only one of these scripts can be run at a time when the website is running.

main.py combines exercises/webpages so all of the blog/exercises can be accessed at once when you run the devserver.

/templates contains the jinga2 templates for the emily-webapp.

/pset 1,2,3 individual scripts contains individual scripts for those psets. each script can be run independently on the devserver if desired (change between scripts by editing app.yaml)
Note: If you're running a pset1,2,3 script by itself you may need to move it to the root folder/edit the directory path in the code to make the templates work.