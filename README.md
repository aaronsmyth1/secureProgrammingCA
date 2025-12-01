# secureProgrammingCA
Hi this is my project for secure programming, a blog post app including secure and insecure versions to demonstrate various vulnerabilities and how they were fixed.
This is the main branch, which will act as a configuration tool to properly start up the app as well as some added context

the insecure app is developed with various vulnerabilites including sql injection flaw, Cross Site Scripting XSS vulnerability: Reflected, DOM Based and Stored and sensitive data exposure
the secure app has patched all these vulnerabilites and has also implemented Cross Site Requested Forgery Token
Proper Session Management incorporated
Use of Security Headers
Adequate logging and monitoring incorporated into the application for added security 

## Prerequisites

- Python 3.x installed
- pip (Python package manager)

to start make sure you have these installed

once they are installed download the project 

install dependencies by opening command line prompt and running -> pip install -r requirements.txt
once that is done you can start the project by running -> python insecureApp.py for the insecure version or -> python secureApp.py for the secure version with vulnerabilites removed



