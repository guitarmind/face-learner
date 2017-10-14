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
import time

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

class CachedDisabledStaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        # Disable cache
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

class DefaultPageHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "text/html; charset=UTF-8")
        with open(os.path.join(os.getcwd(), 'web/index.html')) as f:
            self.write(f.read())
    def set_extra_headers(self, path):
        # Disable cache
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

class FaceDetectionHandler(tornado.web.RequestHandler):
    def post(self):
        data_url = self.request.body
        print(data_url)
        timestamp = time.time()
        self.write({
            "processing_time": timestamp
        })

def main():
    parser = optparse.OptionParser()
    parser.add_option('-p', '--port', dest='port', help='the listening port of Web server (default: 8000)')
    (options, args) = parser.parse_args()

    port = options.port
    if not options.port:   # if port is not given, use the default one 
        port = 8000

    application = tornado.web.Application([
                    (r"/", DefaultPageHandler),
                    (r"/face/detection", FaceDetectionHandler),
                    (r'/deps/css/(.*)',CachedDisabledStaticFileHandler,{'path':"web/deps/css"}),
                    (r'/deps/js/(.*)',CachedDisabledStaticFileHandler,{'path':"web/deps/js"}),
                    (r'/deps/fonts/(.*)',CachedDisabledStaticFileHandler,{'path':"web/deps/fonts"}),
                    (r'/js/(.*)',CachedDisabledStaticFileHandler,{'path':"web/js"})])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)
    logger.info("Web server starts at port " + str(port) + ".")
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
