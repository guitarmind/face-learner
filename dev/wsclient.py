#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import websocket
# import ssl
 
# if __name__ == "__main__":
#     # websocket.enableTrace(True)
#     ws = websocket.create_connection("wss://markpeng-test01.apps.exosite.io/webcam",
#         sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False},
#         origin="http://localhost/",
#         host="localhost")
#     print("Sending 'Hello, World'...")
#     ws.send("Hello, World")
#     result = ws.recv()
#     print result
#     ws.close()

# import websocket
# import thread
# import time

# def on_message(ws, message):
#     print message

# def on_error(ws, error):
#     print error

# def on_close(ws):
#     print "### closed ###"

# def on_open(ws):
#     def run(*args):
#         for i in range(3):
#             time.sleep(1)
#             ws.send("Hello %d" % i)
#         time.sleep(1)
#         ws.close()
#         print "thread terminating..."
#     thread.start_new_thread(run, ())


# if __name__ == "__main__":
#     websocket.enableTrace(True)
#     ws = websocket.WebSocketApp("wss://markpeng-test01.apps.exosite.io/webcam",
#                               on_message = on_message,
#                               on_error = on_error,
#                               on_close = on_close)
#     ws.on_open = on_open
#     ws.run_forever()

# from tornado.ioloop import IOLoop
# from tornado.websocket import websocket_connect

# class WebsocketClient:
#     def __init__(self, url):        
#         websocket_connect(url, callback=self.run)
#         self.stop = False

#     def run(self,future):
#         self.conn = future.result()
#         self.conn.read_message(callback=self.read_msg)

#     def send_msg(self, msg):
#         self.conn.write_message(msg)

#     def read_msg(self, future):
#             print("hihihi")
#             msg = future.result()
#             if msg is None:
#                 print "Server disconnected."
#                 IOLoop.instance().stop()
#             else:
#                 if len(msg) > 0:
#                     print "[Got message] " + msg
#                     self.conn.read_message(callback=self.read_msg)

#                 print "Plese type some words:\n"
#                 input = raw_input()
#                 if input is not None:
#                     if input == "quit()":
#                         print "Closing connection from client ..."
#                         self.conn.close()    
#                         IOLoop.instance().stop()
#                         print "Connection closed."                    
#                     else:
#                         self.send_msg(input)

#                 self.conn.read_future = None
#                 self.conn.read_message(callback=self.read_msg)
                            

# def main():
#     url = "wss://markpeng-test01.apps.exosite.io/webcam"
#     client = WebsocketClient(url)
#     IOLoop.instance().start()

 
# if __name__ == '__main__':
#     main()
