# irc.py - an IRC-like implementation for Portland State University's
#          CS594 - Internetworking Protocols project
#
# Copyright (C) 2017  Jeremiah Peschka <jpeschka@pdx.edu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Client for CS594 project

import common
from datetime import datetime
import threading
import socket
import socketserver
import sys

USAGE = """Usage: python3 client.py <nick> [<server> <port>]"""

helptext = """Available Commands:
/quit                  Disconnect from the server and quit this program
/create <room>         Creates <room>. Does not join <room>
/join <room>           Joins <room>
/msg <room> <message>  Sends <message> to <room>
/ls rooms              List available rooms
/ls users              List available users
/pm <user> <message>   Sends <message> to <user>
/bcast <message>       Sends <message> to all users
"""

SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 8080

DEBUG = True


class IRCClient(socketserver.StreamRequestHandler):
    def __init__(self, nick: str, host: str, port: int):
        self.nick = nick
        self.server = (host, port)

    def connect_and_spin(self):
        self.connect()
        self.spin()

    def connect(self):
        connect = common.Connect(self.nick)
        result = self.send_message(connect)

        if DEBUG:
            print("Message received: " + result.__str__())

        if result.status != common.Status.OK:
            self.display_error("Unable to connect: ", result.error)
            exit(1)

    # TODO implement spin()
    #      This should collect user input and enter an endless loop

    def send_message(self, packet):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(self.server)
            s.send(packet.encode())
            response = common.decode(s.makefile('r').readline().strip())
            s.close()

            if isinstance(response, common.Connect):
                print("Connection successful!")
            elif isinstance(response, common.Disconnect):
                print("Goodbye!")
                sys.exit()
            elif isinstance(response, common.CreateRoom):
                self.display_status_message(
                    "Room " + response.room + " created", response.timestamp)
            elif isinstance(response, common.JoinRoom):
                self.display_status_message("Joined " + response.room,
                                            response.timestamp)
            elif isinstance(response, common.LeaveRoom):
                self.display_status_message("Left " + response.room,
                                            response.timestamp)
            elif isinstance(response, common.MessageRoom):
                self.display_message(response.room, response.username,
                                     response.timestamp)
            elif isinstance(response, common.ListRooms):
                self.display_status_message(
                    "Rooms available:" + "\n\t".join(response.rooms),
                    response.timestamp)
            elif isinstance(response, common.ListUsers):
                self.display_status_message(
                    "Users available:" + "\n\t".join(response.users),
                    response.timestamp)
            elif isinstance(response, common.PrivateMessage):
                self.display_private_message(response.username, response.to,
                                             response.message,
                                             response.timestamp)
            elif isinstance(response, common.Broadcast):
                self.display_broadcast(response.username, response.message,
                                       response.timestamp)
        except TypeError as te:
            print("Error parsing response from server: '" + te.__str__() + "'")

    def display_message(self,
                        room: str,
                        from_user: str,
                        message: str,
                        message_time: datetime = datetime.utcnow()):
        print(message_time.isoformat() + " <" + room + "> " + from_user + ": "
              + message)

    def display_status_message(self,
                               message: str,
                               message_time: datetime = datetime.utcnow()):
        print(message_time.isoformat() + ": " + message)

    def display_error(self, preamble: str, error: common.Error):
        print(preamble + error.to_string())

    def display_private_message(self,
                                from_user: str,
                                to_user: str,
                                message: str,
                                timestamp: datetime = datetime.utcnow()):
        print(timestamp.isoformat() + " PM from " + from_user + ": " + message)

    def display_broadcast(self,
                          from_user: str,
                          message: str,
                          timestamp: datetime = datetime.utcnow()):
        print("\n" + timestamp.isoformat() + " BROADCAST\n\tFrom <" + from_user
              + ">: " + message)


if __name__ == '__main__':
    argc = len(sys.argv)

    if argc == 2:
        username = sys.argv[1]
        server = SERVER_ADDRESS
        port = SERVER_PORT
    elif argc == 4:
        username = sys.argv[1]
        server = sys.argv[2]
        port = sys.argv[3]
    else:
        print(USAGE)
        print(helptext)
        sys.exit()
