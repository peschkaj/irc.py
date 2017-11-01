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

# Common structures for CS594 project

from enum import Enum

UNIT_SEPARATOR = chr(31)


# Operations
class Operations(Enum):
    SERVER_JOIN = 1
    SERVER_PART = 2
    ROOM_CREATE = 3
    ROOM_JOIN = 4
    ROOM_PART = 5
    ROOM_MSG = 6
    ROOM_LIST = 7
    USER_LIST = 8
    USER_MSG = 9
    BROADCAST = 10

    def __str__(self):
        return self.name


# Allowed status messages
class Status(Enum):
    OK = 0
    ERROR = 1

    def __str__(self):
        return self.name

    def to_string(self):
        if self == Status.OK:
            return "OK"
        else:
            return "ERROR"

    @staticmethod
    def from_string(s):
        if s == "OK":
            return Status.OK
        else:
            return Status.ERROR


class Error(Enum):
    UNKNOWN_ERROR = 0
    MALFORMED_MESSAGE = 1
    USER_ALREADY_EXISTS = 2
    USER_NOT_FOUND = 3
    SERVER_BUSY = 4
    ROOM_NOT_FOUND = 5
    ROOM_ALREADY_EXISTS = 6

    def to_string(self):
        if self == Error.MALFORMED_MESSAGE:
            return "Malformed message"
        elif self == Error.USER_ALREADY_EXISTS:
            return "User already exists"
        elif self == Error.USER_NOT_FOUND:
            return "User not found"
        elif self == Error.SERVER_BUSY:
            return "Server busy"
        elif self == Error.ROOM_NOT_FOUND:
            return "Room not found"
        elif self == Error.ROOM_ALREADY_EXISTS:
            return "Room already exists"
        else:
            return "Unknown error"

    @staticmethod
    def to_error(s):
        if s == "Malformed message":
            return Error.MALFORMED_MESSAGE
        elif s == "User already exists":
            return Error.USER_ALREADY_EXISTS
        elif s == "User not found":
            return Error.USER_NOT_FOUND
        elif s == "Server busy":
            return Error.SERVER_BUSY
        elif s == "Room not found":
            return Error.ROOM_NOT_FOUND
        elif s == "Room already exists":
            return Error.ROOM_ALREADY_EXISTS
        elif s is None:
            return None
        else:
            return Error.UNKNOWN_ERROR


class IrcPacket(object):
    def __init__(self, opcode, status=Status.OK, error=None):
        self.opcode = opcode
        self.status = status
        if error is not None:
            self.error = error

    def __str__(self):
        if self.error is None:
            return "{1}{0}{2}".format(UNIT_SEPARATOR, self.opcode.name,
                                      self.status.name)

        return "{1}{0}{2}{0}{3}".format(self.separator, self.opcode.name,
                                        self.status.name, self.error)

    def encode(self):
        return (self.__str__() + "\n").encode()


class Connect(IrcPacket):
    def __init__(self,
                 username,
                 server="127.0.0.1",
                 port="8080",
                 status=Status.OK,
                 error=None):
        super().__init__(Operations.SERVER_JOIN, status, error)
        self.username = username
        self.server = server
        self.port = port

    def __str__(self):
        if self.error is not None:
            return super.__str__()

        return "{1}{0}{2}".format(UNIT_SEPARATOR,
                                  super.__str__(), self.username)

    def encode(self):
        return (self.__str__() + "\n").encode()


class Disconnect(IrcPacket):
    def __init__(self, username, status=Status.OK, error=None):
        super().__init__(Operations.SERVER_PART, status, error)
        self.username = username

    def __str__(self):
        if self.error is not None:
            return super.__str__()

        return "{1}{0}{2}".format(UNIT_SEPARATOR,
                                  super.__str__(), self.username)

    def encode(self):
        return (self.__str__() + "\n").encode()


class CreateRoom(IrcPacket):
    def __init__(self, username, room, status=Status.OK, error=None):
        super().__init__(Operations.ROOM_CREATE, status, error)
        self.username = username
        self.room = room

    def __str__(self):
        if self.error is not None:
            return super.__str__()

        return "{1}{0}{2}{0}{3}".format(UNIT_SEPARATOR,
                                        super.__str__(), self.username,
                                        self.room)

    def encode(self):
        return (self.__str__() + "\n").encode()


class JoinRoom(IrcPacket):
    def __init__(self, username, room, status=Status.OK, error=None):
        super().__init__(Operations.ROOM_JOIN, status, error)
        self.username = username
        self.room = room

    def __str__(self):
        if self.error is not None:
            return super.__str__()

        return "{1}{0}{2}{0}{3}".format(UNIT_SEPARATOR,
                                        super.__str__(), self.username,
                                        self.room)

    def encode(self):
        return (self.__str__() + "\n").encode()


class LeaveRoom(IrcPacket):
    def __init__(self, username, room, status=Status.OK, error=None):
        super().__init__(Operations.ROOM_PART, status, error)
        self.username = username
        self.room = room

    def __str__(self):
        if self.error is not None:
            return super.__str__()

        return "{1}{0}{2}{0}{3}".format(UNIT_SEPARATOR,
                                        super.__str__(), self.username,
                                        self.room)

    def encode(self):
        return (self.__str__() + "\n").encode()


class ListRooms(IrcPacket):
    def __init__(self, rooms=[], status=Status.OK, error=None):
        super().__init__(Operations.ROOM_LIST, status, error)
        self.rooms = rooms

    def __str__(self):
        if self.error is not None:
            return super.__str__()

        return "{1}{0}{2}".format(UNIT_SEPARATOR,
                                  super.__str__(), ",".join(self.rooms))

    def encode(self):
        return (self.__str__() + "\n").encode()


class MessageRoom(IrcPacket):
    def __init__(self, username, room, message, status=Status.OK, error=None):
        super().__init__(Operations.ROOM_MSG, status, error)
        self.username = username
        self.room = room
        self.message = message

    def __str__(self):
        if self.error is not None:
            return super.__str__()

        return "{1}{0}{2}{0}{3}{0}{4}".format(UNIT_SEPARATOR,
                                              super.__str__(), self.username,
                                              self.room, self.message)

    def encode(self):
        return (self.__str__() + "\n").encode()
