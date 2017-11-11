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

# Server for CS594 project

from typing import List
import common
import socket
import socketserver
import sys
import signal


class User(object):
    def __init__(self, nick: str, host: str, port: int):
        self.nick = nick
        self.host = host
        self.port = port


class Room(object):
    def __init__(self, name, users: List[str] = None):
        if users is None:
            self.users = []
        else:
            self.users = [users]
        self.name = name

    def add_to_room(self, user: User):
        self.users.append(user)

    def remove_user(self, user: User):
        self.users.remove(user)

    def contains_user(self, username):
        for user in self.users:
            if user == username:
                return True

        return False

    def __str__(self):
        return self.room.name


USERS: List[User] = list()
ROOMS: List[Room] = list()

LISTEN_ADDRESS = "127.0.0.1"
LISTEN_PORT = 8080
SERVER_SOCKET = None
DEBUG = True


# TODO: This needs to send all users a message that they're being removed
# TODO: This needs to close down the server socket
def interrupt_handler(signal, frame):
    SERVER_SOCKET.close()
    for user in USERS:
        IRCServer.send_message(common.Disconnect, user)
    sys.exit(0)


signal.signal(signal.SIGINT, interrupt_handler)


class IRCServer(socketserver.StreamRequestHandler):
    @staticmethod
    def handle_connect(packet: common.Connect, address):
        for user in USERS:
            if user.nick == packet.username:
                packet.status = common.Status.ERROR
                packet.error = common.Error.USER_ALREADY_EXISTS
                return packet

        USERS.append(User(packet.username, address[1], packet.port))
        packet.status = common.Status.OK
        packet.error = common.Error.NO_ERROR
        return packet

    @staticmethod
    def handle_disconnect(packet: common.Disconnect):
        for user in USERS:
            if user.nick == packet.username:
                USERS.removegs(user)
                for room in ROOMS:
                    room.remove_user(packet.username)
                packet.status = common.Status.OK
                packet.error = common.Error.NO_ERROR
                return packet

        packet.status = common.Status.ERROR
        packet.error = common.Error.USER_NOT_FOUND
        return packet

    @staticmethod
    def handle_create_room(packet: common.CreateRoom):
        for room in ROOMS:
            if room.name == packet.room:
                packet.status = common.Status.ERROR
                packet.error = common.Error.ROOM_ALREADY_EXISTS
                return packet

        ROOMS.append(Room(packet.room, [packet.username]))
        packet.status = common.Status.OK
        packet.error = common.Error.NO_ERROR
        return packet

    @staticmethod
    def handle_join_room(packet: common.JoinRoom):
        print("In handle_join_room")
        for room in ROOMS:
            if room.name == packet.room:
                if DEBUG:
                    print("found room")
                room.add_to_room(packet.username)
                packet.status = common.Status.OK
                packet.error = common.Error.NO_ERROR
                return packet

        packet.status = common.Status.ERROR
        packet.error = common.Error.ROOM_NOT_FOUND
        return packet

    @staticmethod
    def handle_leave_room(packet: common.LeaveRoom):
        for room in ROOMS:
            if room.name == packet.room:
                room.remove_user(packet.username)
                packet.status = common.Status.OK
                packet.error = common.Error.NO_ERROR
                return packet

        packet.status = common.Status.ERROR
        packet.error = common.Error.ROOM_NOT_FOUND
        return packet

    def handle_message_room(self, packet: common.MessageRoom):
        if DEBUG:
            print("In handle_message_room")
        for room in ROOMS:
            if room.name == packet.room:
                if DEBUG:
                    print("  Found room")
                for user in USERS:
                    if room.contains_user(user.nick):
                        self.send_message(packet, user)
                return packet

        packet.status = common.Status.ERROR
        packet.error = common.Error.ROOM_NOT_FOUND
        return packet

    def handle_private_message(self, packet: common.PrivateMessage):
        for user in USERS:
            if user.nick == packet.to:
                self.send_message(packet, user)
                return packet

        packet.status = common.Status.ERROR
        packet.error = common.Error.USER_NOT_FOUND

    @staticmethod
    def handle_list_rooms(packet: common.ListRooms):
        packet.rooms = list()
        for room in ROOMS:
            packet.rooms.append(room)

        packet.status = common.Status.OK
        packet.error = common.Error.NO_ERROR
        return packet

    @staticmethod
    def handle_list_users(packet: common.ListUsers):
        packet.users = list()
        for user in USERS:
            packet.users.append(user.nick)

        packet.status = common.Status.OK
        packet.error = common.Error.NO_ERROR
        return packet

    @staticmethod
    def send_message(packet: common.IrcPacket, user: User):
        if DEBUG:
            print("In send_message " + packet.__str__())
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if DEBUG:
                print("\tSending message to " + user.host + ":" + str(
                    user.port))
            s.connect((user.host, user.port))
            s.send(packet.encode())
            s.close()
        except socket.error as e:
            if e.errno == 111:
                if user in USERS:
                    USERS.remove(user)
            else:
                print(e)

    def handle_broadcast(self, packet: common.Broadcast):
        for user in USERS:
            self.send_message(packet, user)
        return packet

    def handle(self):
        #input = self.rfile.readline().decode().strip()
        new_input = self.rfile.readline()

        address = self.connection.getpeername()

        try:
            message = common.decode(new_input)
        except TypeError as te:
            print("Error processing packet: '" + input + "' generated error '"
                  + te.__str__() + "'")

        try:
            if isinstance(message, common.Connect):
                message = self.handle_connect(message,
                                              (message.username, address))
            elif isinstance(message, common.Disconnect):
                message = self.handle_disconnect(message)
            elif isinstance(message, common.CreateRoom):
                message = self.handle_create_room(message)
            elif isinstance(message, common.JoinRoom):
                print("***Received Join Room***")
                message = self.handle_join_room(message)
            elif isinstance(message, common.LeaveRoom):
                message = self.handle_leave_room(message)
            elif isinstance(message, common.MessageRoom):
                print("***Received Message Room***")
                message = self.handle_message_room(message)
            elif isinstance(message, common.ListRooms):
                message = self.handle_list_rooms(message)
            elif isinstance(message, common.ListUsers):
                message = self.handle_list_users(message)
            elif isinstance(message, common.PrivateMessage):
                message = self.handle_private_message(message)
            elif isinstance(message, common.Broadcast):
                message = self.handle_broadcast(message)
            else:
                message.status = common.Status.ERROR
                message.error = common.Error.MALFORMED_MESSAGE
        except TypeError as te:
            message.status = common.Status.ERROR
            message.error = common.Error.MALFORMED_MESSAGE
            print("Error in message router: '" + te.__str__() + "'")

        self.wfile.write(message.encode())
        return


if __name__ == "__main__":
    with socketserver.ThreadingTCPServer((LISTEN_ADDRESS, LISTEN_PORT),
                                         IRCServer) as server:
        SERVER_SOCKET = server.socket
        print("Server started on " + str(LISTEN_ADDRESS) + ":" +
              str(LISTEN_PORT))
        server.serve_forever()
