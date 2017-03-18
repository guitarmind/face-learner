#!/usr/bin/env python
#
# A simple Web server for static files.
#
# Author: Mark Peng (markpeng.ntu@gmail.com)
#

import tornado.httpserver
import tornado.ioloop
import tornado.web
import optparse
import logging
import os

"""
Logging settings
"""
log_file = "face-learner.access.log"
logger = logging.getLogger('FaceLearner')
logger.setLevel(logging.INFO)
try:
    os.remove(log_file)
except OSError:
    pass
fileHandler = logging.FileHandler(log_file)
fileHandler.setLevel(logging.INFO)
# console handler
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S')
fileHandler.setFormatter(formatter)
consoleHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.addHandler(consoleHandler)

def main():
    parser = optparse.OptionParser()
    parser.add_option('-p', '--port', dest='port', help='the listening port of Web server (default: 8000)')
    (options, args) = parser.parse_args()

    port = options.port
    if not options.port:   # if port is not given, use the default one 
      port = 8000

    application = tornado.web.Application([
                    (r"/(.*)", tornado.web.StaticFileHandler, {"path": ".", "default_filename": "index.html"}),
                    (r'/css/(.*)',tornado.web.StaticFileHandler,{'path':"deps/css"}),
                    (r'/js/(.*)',tornado.web.StaticFileHandler,{'path':"deps/js"}),
                    (r'/fonts/(.*)',tornado.web.StaticFileHandler,{'path':"deps/fonts"}),
                    (r'/css/(.*)',tornado.web.StaticFileHandler,{'path':"css"}),
                    (r'/js/(.*)',tornado.web.StaticFileHandler,{'path':"js"}),
                    (r'/img/(.*)',tornado.web.StaticFileHandler,{'path':"img"})])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)
    logger.info("Web server starts at port " + str(port) + ".")
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
