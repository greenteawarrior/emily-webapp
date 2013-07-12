#meant to be imported

class HelloPage(Handler):
    def get(self):
        self.write("Hello, Udacity!")