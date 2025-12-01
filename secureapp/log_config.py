import logging

def setupLogging():
    logging.basicConfig(
        filename='app.log',
        level=logging.INFO,  
        format='%(asctime)s %(levelname)s:%(message)s'
        )