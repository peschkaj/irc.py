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
from dateutil import tz
import random
import socket
import socketserver
import sys
import threading
from typing import Tuple, List

DEBUG = False

USAGE = """Usage: python3 client.py <nick> [<server> <port> [<low_port> <high_port>]]

    <low_port> and <high_port> are used to designate a random port for
    the client to listen on. If they are not supplied, the default values
    of 45679 and 45965 are used for the range. These ports are listed as
    available on macOS 10.13
"""

helptext = """Available Commands:
/quit                  Disconnect from the server and quit this program
/create <room>         Creates <room>. Does not join <room>
/join <room>           Joins <room>
/leave <room>          Leaves <room>
/msg <room> <message>  Sends <message> to <room>
/ls rooms              List available rooms
/ls users              List available users
/ls usersin <room>     List available users present in <room>
/pm <user> <message>   Sends <message> to <user>
/bcast <message>       Sends <message> to all users
"""

INVALID_COMMAND = """
Invalid command. You can always type /help for a list of valid commands
and their usage. Here, let me do that for you now...
"""

USERNAME: str = ""
SERVER_ADDRESS: str = "127.0.0.1"
SERVER_PORT: int = 8080
LOW_PORT: int = 45679
HIGH_PORT: int = 45965
LISTEN_PORT: int
SERVER: Tuple[str, int]
TO_ZONE = tz.tzlocal()
FROM_ZONE = tz.tzutc()


class IRCClient(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            data = self.rfile.readline()
            message = common.decode(data)

            self.handle_server_message(message)
        except SystemError as se:
            print("System error encountered!")
            print(se)
            sys.exit(1)

    def handle_server_message(self, message: common.IrcPacket):
        if DEBUG:
            print("In handle_server_message")
            print("\tmessage is '" + message.__str__() + "'")
        if isinstance(message, common.Connect):
            print("Connection successful!")
        elif isinstance(message, common.Disconnect):
            print("You have been disconnected. Goodbye!")
            sys.exit(0)
        elif isinstance(message, common.CreateRoom):
            display_status_message("Room " + message.room + " created",
                                   message.timestamp)
        elif isinstance(message, common.JoinRoom):
            display_status_message("Joined " + message.room, message.timestamp)
        elif isinstance(message, common.LeaveRoom):
            display_status_message("Left " + message.room, message.timestamp)
        elif isinstance(message, common.MessageRoom):
            if message.status == common.Status.OK:
                display_message(message.room, message.username,
                                message.message, message.timestamp)
            else:
                display_error("Unable to message '" + message.room + "'",
                              message.error)
        elif isinstance(message, common.PrivateMessage):
            display_private_message(message.username, message.to,
                                    message.message, message.timestamp)
        elif isinstance(message, common.Broadcast):
            display_broadcast(message.username, message.message,
                              message.timestamp)


def utc_to_local(utc: datetime):
    return utc.replace(tzinfo=FROM_ZONE).astimezone(TO_ZONE)


def event_loop(username, port):
    while True:
        connect_request = common.Connect(username, port)
        send_message(connect_request)

        if connect_request.error == common.Error.NO_ERROR:
            break
        elif connect_request.error == common.Error.USER_ALREADY_EXISTS:
            print("Username already in use on the server")
            username = input("New username: ").strip()
            while username.find(' ') != -1 and username.find(
                    common.UNIT_SEPARATOR) != -1:
                print("Illegal characters in username.")
                username = input("New username: ").strip()

    while True:
        command = input(username + "> ").strip()
        if command == "/quit":
            quit_server()
            break
        elif command.startswith("/create"):
            create_room(command)
        elif command.startswith("/join"):
            join_room(command)
        elif command.startswith("/leave"):
            leave_room(command)
        elif command.startswith("/msg"):
            message_room(command)
        elif command == "/ls rooms":
            list_rooms()
        elif command == "/ls users":
            list_users()
        elif command.startswith("/ls usersin"):
            list_users_in_room(command)
        elif command.startswith("/pm"):
            private_message(command)
        elif command.startswith("/bcast"):
            broadcast(command)
        elif command == "/help":
            print(helptext)
        else:
            print(INVALID_COMMAND)
            print(helptext)


def quit_server():
    disco = common.Disconnect(USERNAME)
    send_message(disco)
    print("Exiting program")


def create_room(command: str):
    room = command[8:].strip()
    if len(room) < 1:
        print("You didn't enter a valid room name.")
        return
    if room.find(' ') != -1:
        print("Invalid room name, no spaces allowed")
        return
    cr = common.CreateRoom(room, USERNAME)
    send_message(cr)


def join_room(command: str):
    room = command[5:].strip()
    if len(room) < 1 or room.find(' ') != -1 or room.find(
            common.UNIT_SEPARATOR) != -1:
        print("Enter a valid room name")
        return
    jr = common.JoinRoom(room, USERNAME)
    send_message(jr)


def leave_room(command: str):
    command = command[6:].strip()
    parts = command.split(' ')
    if len(parts) < 1:
        print("Enter a room to leave")
        return
    elif len(parts) > 1:
        print(
            "You've entered more than one room. I will only leave the first room."
        )

    room = parts[0]
    lr = common.LeaveRoom(room, USERNAME)
    send_message(lr)


def message_room(command: str):
    command = command[4:].strip()
    parts = command.split(' ')
    if len(parts) < 2:
        print("Enter a valid message")
        return

    room = parts[0]
    message = " ".join(parts[1:])
    if len(message) < 1 or message.find(common.UNIT_SEPARATOR) != -1:
        print("Enter a valid message")
        return

    msg = common.MessageRoom(room, message, USERNAME)
    send_message(msg)


def list_rooms():
    rooms: List[str] = list()
    send_message(common.ListRooms(rooms, USERNAME))


def list_users():
    users: List[str] = list()
    send_message(common.ListUsers(users, USERNAME))


def list_users_in_room(command: str):
    users: List[str] = list()
    room = command[11:].strip()
    if len(room) < 1 or room.find(' ') != -1 or room.find(
            common.UNIT_SEPARATOR) != -1:
        print("Enter a valid room")
        return
    send_message(common.ListUsersInRoom(users, room, USERNAME))


def private_message(command: str):
    command = command[3:].strip()
    parts = command.split(' ')
    if len(parts) < 2:
        print("Enter a valid private message.")
        print("Format: /pm <to> <message")

    to = parts[0]
    message = " ".join(parts[1:])

    if len(message) < 1 or message.find(common.UNIT_SEPARATOR) != -1:
        print("Enter a valid message")
        return

    pm = common.PrivateMessage(USERNAME, to, message)
    if DEBUG:
        print("\t" + pm.__str__())
    send_message(pm)


def broadcast(command: str):
    message = command[6:].strip()
    if len(message) < 1 or message.find(common.UNIT_SEPARATOR) != -1:
        print("Enter a valid message")
        return

    bcast = common.Broadcast(message, USERNAME)
    send_message(bcast)


def send_message(packet: common.IrcPacket):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(SERVER)
        s.send(packet.encode())
        raw_response = s.makefile('r').readline()

        if DEBUG:
            print("Received message from server: '" + raw_response + "'")

        response = common.decode(raw_response.encode())
        s.close()

        handle_message(response)
    except TypeError as te:
        print("Error parsing response from server: '" + te.__str__() + "'")


def handle_message(message: common.IrcPacket):
    if DEBUG:
        print("In handle_message")

    if isinstance(message, common.Connect):
        print("Connection successful!")
    elif isinstance(message, common.Disconnect):
        print("You have been disconnected. Goodbye!")
        sys.exit(0)
    elif isinstance(message, common.CreateRoom):
        if message.status == common.Status.ERROR:
            display_error("Error creating room '" + message.room + "'",
                          message.error)
            return

        display_status_message("Room " + message.room + " created",
                               message.timestamp)
    elif isinstance(message, common.JoinRoom):
        if message.status == common.Status.ERROR:
            display_error("Error joining room '" + message.room + "'",
                          message.error)
        display_status_message("Joined " + message.room, message.timestamp)
    elif isinstance(message, common.LeaveRoom):
        display_status_message("Left " + message.room, message.timestamp)
    elif isinstance(message, common.MessageRoom):
        # We only check for errors here since. If our message is successful,
        # we'll get a response from the server that displays our message on
        # screen.
        if message.status == common.Status.ERROR:
            display_error("Unable to message '" + message.room + "'",
                          message.error)
    elif isinstance(message, common.ListRooms):
        if message.status == common.Status.ERROR:
            display_error("Unable to list rooms.", message.error)
            return

        rooms = message.rooms
        if len(rooms) > 0:
            display_status_message(
                "Rooms available:" + "\n\t".join(message.rooms),
                message.timestamp)
        else:
            display_status_message(
                "No rooms available. Create one with `/create <room>`.")
    elif isinstance(message, common.ListUsers):
        display_status_message("Users available: " + ", ".join(message.users),
                               message.timestamp)
    elif isinstance(message, common.ListUsersInRoom):
        if message.status == common.Status.ERROR:
            display_error(
                "Unable to list users in room '" + message.room + "'",
                message.error)
            return

        if len(message.users) == 0:
            display_status_message("Room '" + message.room + "' is empty.")
            return

        display_status_message(
            "Users in '" + message.room + "': \n\t" + ", ".join(message.users),
            message.timestamp)
    elif isinstance(message, common.PrivateMessage):
        if message.status == common.Status.ERROR:
            display_error("Unable to send private message.", message.error)
            return
        display_private_message(message.username, message.to, message.message,
                                message.timestamp)
    # elif isinstance(message, common.Broadcast):
    #     display_broadcast(message.username, message.message, message.timestamp)


def display_message(room: str,
                    from_user: str,
                    message: str,
                    message_time: datetime = datetime.utcnow()):
    print(
        utc_to_local(message_time).strftime("%Y-%m-%d %H:%M") + " <" + room +
        "> " + from_user + ": " + message)


def display_status_message(message: str,
                           message_time: datetime = datetime.utcnow()):
    print(
        utc_to_local(message_time).strftime("%Y-%m-%d %H:%M") + ": " + message)


def display_error(preamble: str, error: common.Error):
    print(preamble + ": " + error.to_string())


def display_private_message(from_user: str,
                            to_user: str,
                            message: str,
                            timestamp: datetime = datetime.utcnow()):
    print(
        utc_to_local(timestamp).strftime("%Y-%m-%d %H:%M") + " PM " + from_user
        + " -> " + to_user + ": " + message)


def display_broadcast(from_user: str,
                      message: str,
                      timestamp: datetime = datetime.utcnow()):
    print("\n" + utc_to_local(timestamp).strftime("%Y-%m-%d %H:%M") +
          " BROADCAST\n\tFrom <" + from_user + ">: " + message)


def random_port_in_range(low: int, high: int):
    return random.randrange(low, high)


if __name__ == '__main__':
    argc = len(sys.argv)

    if argc == 2:
        USERNAME = sys.argv[1].strip()
    elif argc == 4:
        USERNAME = sys.argv[1].strip()
        SERVER_ADDRESS = sys.argv[2].strip()
        SERVER_PORT = int(sys.argv[3].strip())
        low_port = LOW_PORT
        high_port = HIGH_PORT
    elif argc == 6:
        USERNAME = sys.argv[1].strip()
        SERVER_ADDRESS = sys.argv[2].strip()
        SERVER_PORT = int(sys.argv[3].strip())
        LOW_PORT = int(sys.argv[4].strip())
        HIGH_PORT = int(sys.argv[5].strip())
    else:
        print(USAGE)
        print(helptext)
        sys.exit()

    LISTEN_PORT = random_port_in_range(LOW_PORT, HIGH_PORT)
    SERVER = (SERVER_ADDRESS, SERVER_PORT)

    print("Attempting to connect to " + str(SERVER_ADDRESS) + ":" +
          str(SERVER_PORT))
    print("Listening on port " + str(LISTEN_PORT))

    client = socketserver.ThreadingTCPServer(("127.0.0.1", LISTEN_PORT),
                                             IRCClient)
    ct = threading.Thread(target=client.serve_forever)
    ct.daemon = True
    ct.start()

    event_loop(USERNAME, LISTEN_PORT)
