import argparse
import errno
import os
import re
import socket
import SocketServer
import subprocess
import time
import threading
import unittest

import helpers

class ThreadingTCPServer(SocketServer.ThreadingMixIn,SocketServer.TCPServer):
    dispatcher_server = None
    last_communication = None
    busy = False
    dead = False

class TestHandler(SocketServer.BaseRequestHandler):
    command_re = re.compile(r"(\w+)(:.+)*")

    def run_tests(self, commit_id, repo_folder):
        output = subprocess.check_output(["./test_runner_script.sh",
                                        repo_folder, commit_id])
        print output

        test_folder = os.path.join(repo_folder, "tests");
        suite = unittest.TestLoader().discover(test_folder)
        result_file = open("results", "w+")
        unittest.TextTestRunner(result_file).run(suite)
        result_file.close()
        result_file = open("results", "r")
        output = result_file.read()
        helpers.communicate(self.server.dispatcher_server["host"],
                        int(self.server.dispatcher_server["port"],
                        "results:%s:%s:%s" % (commit_id, len(output), output)))

    def handle(self):
        self.data = self.request.recv(1024).strip()
        command_groups = self.command_re.match(self.data)
        if not command_groups:
            self.request.sendall("Invalid command")
            return
        command = command_groups.group(1)

        if command == "ping":
            print "pinged"
            self.server.last_communication = time.time();
            self.request.sendall("pong")
        elif command == "runtest":
            print "got runtest command: am I busy %s" % self.server.busy
            if self.server.busy:
                sle.request.sendall("Busy")
            else:
                self.request.sendall("OK")
                print "running"
                commit_id = command_groups.group(2)[1:]
                self.server.busy = True
                self.run_tests(commit_id,
                        self.server.repo_folder)
                self.server.busy = False
        else:
            self.request.sendall("Invalid command")

def server():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host",
            help="runners host, default it uses localhost",
            default="localhost",
            action="store")
    parser.add_argument("--port",
            help="runner port,default it uses 8900",
            default=8900,
            action="store")
    parser.add_argument("--dispatcher-server",
            help="dispatcher host:port, byd default it uses 'localhost:8000'",
            default="localhost:8888",
            action="store")
    parser.add_argument("repo", metavar="REPO", type=str,
            help="path to the repository this will observe")
    args = parser.parse_args()
    dispatcher_host, dispatcher_port = args.dispatcher_server.split(":")

    server = ThreadingTCPServer((args.host, int(args.port)), TestHandler)
    server.repo_folder = args.repo
    server.dispatcher_server = {"host": dispatcher_host, "port": dispatcher_port}

    response = helpers.communicate(server.dispatcher_server["host"], 
            int(server.dispatcher_server["port"]),
            "register:%s:%s"%(args.host, args.port))

    if response != "OK":
        raise Exception("can't register with dispatcher!")

    print 'test runner serving on %s:%s' % (args.host, int(args.port))

    def dispatcher_checker(server):
        while not server.dead:
            time.sleep(5)
            if (time.time() - server.last_communication) > 10:
                try:
                    response = helpers.communicate(server.dispatcher_server["host"],
                            int(server.dispatcher_server["port"],
                            "status"))
                    if response != "OK":
                        print "Dispatcher is no longer functional"
                        server.shutdown()
                        return
                except socket.error as e:
                    print "can't communicate with dispatcher: %s" % e
                    server.shutdown()
                    return

    t = threading.Thread(target=dispatcher_checker, args=(server,))

    try:
        t.start()
        server.serve_forever()
    except (KeyboardInterrupt, Exception):
        server.dead = True
        t.join()

if __name__ == "__main__":
    server()

