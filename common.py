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

from typing import List
from enum import Enum
import datetime
import dateutil.parser
import unittest

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
    NO_ERROR = 0
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
    def __init__(self,
                 opcode: Operations,
                 username: str,
                 timestamp: datetime = datetime.datetime.utcnow(),
                 status: Status = Status.OK,
                 error: Error = Error.NO_ERROR):
        self.opcode = opcode
        self.status = status
        self.username = username
        self.timestamp = timestamp
        self.error = error

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

    def __str__(self):
        return "{1}{0}{2}{0}{3}{0}{4}{0}{5}".format(
            UNIT_SEPARATOR,
            self.opcode.value,
            self.status.value,
            self.error.value,
            self.username,
            self.timestamp.isoformat(),
        )

    def to_string(self):
        return "{1}{0}{2}{0}{3}{0}{4}{0}{5}".format(
            UNIT_SEPARATOR,
            self.opcode.value,
            self.status.value,
            self.error.value,
            self.username,
            self.timestamp.isoformat(),
        )

    def encode(self):
        return (self.__str__() + "\n").encode()


class Connect(IrcPacket):
    def __init__(self,
                 username: str,
                 port: int,
                 timestamp: datetime = datetime.datetime.utcnow(),
                 status: Status = Status.OK,
                 error: Error = Error.NO_ERROR):
        super().__init__(Operations.SERVER_JOIN, username, timestamp, status,
                         error)
        self.port = port

    def __str__(self):
        return "{1}{0}{2}{0}{3}{0}{4}{0}{5}{0}{6}".format(
            UNIT_SEPARATOR,
            self.opcode.value,
            self.status.value,
            self.error.value,
            self.username,
            self.port,
            self.timestamp.isoformat(),
        )

    def encode(self):
        return (self.__str__() + "\n").encode()


class Disconnect(IrcPacket):
    def __init__(self,
                 username: str,
                 timestamp: datetime = datetime.datetime.utcnow(),
                 status: Status = Status.OK,
                 error: Error = Error.NO_ERROR):
        super().__init__(Operations.SERVER_PART, username, timestamp, status,
                         error)

    def __str__(self):
        return "{1}{0}{2}{0}{3}{0}{4}{0}{5}".format(
            UNIT_SEPARATOR,
            self.opcode.value,
            self.status.value,
            self.error.value,
            self.username,
            self.timestamp.isoformat(),
        )

    def encode(self):
        return (self.__str__() + "\n").encode()


class CreateRoom(IrcPacket):
    def __init__(self,
                 room: str,
                 username: str,
                 timestamp: datetime = datetime.datetime.utcnow(),
                 status: Status = Status.OK,
                 error: Error = Error.NO_ERROR):
        super().__init__(Operations.ROOM_CREATE, username, timestamp, status,
                         error)
        self.room = room

    def __str__(self):
        return "{1}{0}{2}{0}{3}{0}{4}{0}{5}{0}{6}".format(
            UNIT_SEPARATOR, self.opcode.value, self.status.value,
            self.error.value, self.username,
            self.timestamp.isoformat(), self.room)

    def encode(self):
        return (self.__str__() + "\n").encode()


class JoinRoom(IrcPacket):
    def __init__(self,
                 room: str,
                 username: str,
                 timestamp: datetime = datetime.datetime.utcnow(),
                 status: Status = Status.OK,
                 error: Error = Error.NO_ERROR):
        super().__init__(Operations.ROOM_JOIN, username, timestamp, status,
                         error)
        self.room = room

    def __str__(self):
        return "{1}{0}{2}{0}{3}{0}{4}{0}{5}{0}{6}".format(
            UNIT_SEPARATOR, self.opcode.value, self.status.value,
            self.error.value, self.username,
            self.timestamp.isoformat(), self.room)

    def encode(self):
        return (self.__str__() + "\n").encode()


class LeaveRoom(IrcPacket):
    def __init__(self,
                 room: str,
                 username: str,
                 timestamp: datetime = datetime.datetime.utcnow(),
                 status: Status = Status.OK,
                 error: Error = Error.NO_ERROR):
        super().__init__(Operations.ROOM_PART, username, timestamp, status,
                         error)
        self.room = room

    def __str__(self):
        return "{1}{0}{2}{0}{3}{0}{4}{0}{5}{0}{6}".format(
            UNIT_SEPARATOR, self.opcode.value, self.status.value,
            self.error.value, self.username,
            self.timestamp.isoformat(), self.room)

    def encode(self):
        return (self.__str__() + "\n").encode()


class ListRooms(IrcPacket):
    def __init__(self,
                 rooms: List[str],
                 username: str,
                 timestamp: datetime = datetime.datetime.utcnow(),
                 status: Status = Status.OK,
                 error: Error = Error.NO_ERROR):
        super().__init__(Operations.ROOM_LIST, username, timestamp, status,
                         error)
        self.rooms = rooms

    def __str__(self):
        return "{1}{0}{2}{0}{3}{0}{4}{0}{5}{0}{6}".format(
            UNIT_SEPARATOR, self.opcode.value, self.status.value,
            self.error.value, self.username,
            self.timestamp.isoformat(), ",".join(self.rooms))

    def encode(self):
        return (self.__str__() + "\n").encode()


class MessageRoom(IrcPacket):
    def __init__(self,
                 room: str,
                 message: str,
                 username: str,
                 timestamp: datetime = datetime.datetime.utcnow(),
                 status: Status = Status.OK,
                 error: Error = Error.NO_ERROR):
        super().__init__(Operations.ROOM_MSG, username, timestamp, status,
                         error)
        self.room = room
        self.message = message

    def __str__(self):
        return "{1}{0}{2}{0}{3}{0}{4}{0}{5}{0}{6}{0}{7}".format(
            UNIT_SEPARATOR, self.opcode.value, self.status.value,
            self.error.value, self.username,
            self.timestamp.isoformat(), self.room, self.message)

    def encode(self):
        return (self.__str__() + "\n").encode()


class ListUsers(IrcPacket):
    def __init__(self,
                 users: List[str],
                 username: str,
                 timestamp: datetime = datetime.datetime.utcnow(),
                 status: Status = Status.OK,
                 error: Error = Error.NO_ERROR):
        super().__init__(Operations.USER_LIST, username, timestamp, status,
                         error)
        self.users = users

    def __str__(self):
        return "{1}{0}{2}{0}{3}{0}{4}{0}{5}{0}{6}".format(
            UNIT_SEPARATOR, self.opcode.value, self.status.value,
            self.error.value, self.username,
            self.timestamp.isoformat(), ",".join(self.users))

    def encode(self):
        return (self.__str__() + "\n").encode()


class PrivateMessage(IrcPacket):
    def __init__(self,
                 username: str,
                 to: str,
                 message: str,
                 timestamp: datetime = datetime.datetime.utcnow(),
                 status: Status = Status.OK,
                 error: Error = Error.NO_ERROR):
        super().__init__(Operations.USER_MSG, username, timestamp, status,
                         error)
        self.to = to
        self.message = message

    def __str__(self):
        return "{1}{0}{2}{0}{3}{0}{4}{0}{5}{0}{6}{0}{7}".format(
            UNIT_SEPARATOR, self.opcode.value, self.status.value,
            self.error.value, self.username,
            self.timestamp.isoformat(), self.to, self.message)

    def encode(self):
        return (self.__str__() + "\n").encode()


class Broadcast(IrcPacket):
    def __init__(self,
                 message: str,
                 username: str,
                 timestamp: datetime = datetime.datetime.utcnow(),
                 status: Status = Status.OK,
                 error: Error = Error.NO_ERROR):
        super().__init__(Operations.BROADCAST, username, timestamp, status,
                         error)
        self.message = message

    def __str__(self):
        return "{1}{0}{2}{0}{3}{0}{4}{0}{5}{0}{6}".format(
            UNIT_SEPARATOR, self.opcode.value, self.status.value,
            self.error.value, self.username,
            self.timestamp.isoformat(), self.message)

    def encode(self):
        return (self.__str__() + "\n").encode()


def decode(packet: bytes):
    pieces = packet.decode().strip().split(UNIT_SEPARATOR)
    msg_type = int(pieces[0])

    # field order: opcode, status, error, username, timestamp
    if msg_type == 1:
        return Connect(pieces[3],
                       int(pieces[4]),
                       dateutil.parser.parse(pieces[5]),
                       Status(int(pieces[1])), Error(int(pieces[2])))
    elif msg_type == 2:
        return Disconnect(pieces[3],
                          dateutil.parser.parse(pieces[4]),
                          Status(int(pieces[1])), Error(int(pieces[2])))
    elif msg_type == 3:
        return CreateRoom(pieces[5], pieces[3],
                          dateutil.parser.parse(pieces[4]),
                          Status(int(pieces[1])), Error(int(pieces[2])))
    elif msg_type == 4:
        return JoinRoom(pieces[5], pieces[3],
                        dateutil.parser.parse(pieces[4]),
                        Status(int(pieces[1])), Error(int(pieces[2])))
    elif msg_type == 5:
        return LeaveRoom(pieces[5], pieces[3],
                         dateutil.parser.parse(pieces[4]),
                         Status(int(pieces[1])), Error(int(pieces[2])))
    elif msg_type == 6:
        return MessageRoom(pieces[5], pieces[6], pieces[3],
                           dateutil.parser.parse(pieces[4]),
                           Status(int(pieces[1])), Error(int(pieces[2])))
    elif msg_type == 7:
        room_list = []
        if (len(pieces) > 5):
            room_list.extend(pieces[5].split(','))

        return ListRooms(room_list, pieces[3],
                         dateutil.parser.parse(pieces[4]),
                         Status(int(pieces[1])), Error(int(pieces[2])))
    elif msg_type == 8:
        user_list = []
        if (len(pieces) > 5):
            user_list.extend(pieces[5].split(','))

        return ListUsers(user_list, pieces[3],
                         dateutil.parser.parse(pieces[4]),
                         Status(int(pieces[1])), Error(int(pieces[2])))
    elif msg_type == 9:
        return PrivateMessage(pieces[3], pieces[5], pieces[6],
                              dateutil.parser.parse(pieces[4]),
                              Status(int(pieces[1])), Error(int(pieces[2])))
    elif msg_type == 10:
        return Broadcast(pieces[5], pieces[3],
                         dateutil.parser.parse(pieces[4]),
                         Status(int(pieces[1])), Error(int(pieces[2])))

    raise TypeError


class TestCommon(unittest.TestCase):
    def test_Connect(self):
        p = Connect("some_user", 8081)
        ep = p.encode()
        dp = decode(ep)
        self.assertEqual(p, dp)

    def test_Disconnect(self):
        p = Disconnect("some_user")
        ep = p.encode()
        dp = decode(ep)
        self.assertEqual(p, dp)

    def test_CreateRoom(self):
        p = CreateRoom("some_user", "room")
        ep = p.encode()
        dp = decode(ep)
        self.assertEqual(p, dp)

    def test_JoinRoom(self):
        p = JoinRoom("some_user", "room")
        ep = p.encode()
        dp = decode(ep)
        self.assertEqual(p, dp)

    def test_LeaveRoom(self):
        p = LeaveRoom("some_user", "room")
        ep = p.encode()
        dp = decode(ep)
        self.assertEqual(p, dp)

    def test_ListRooms_empty(self):
        p = ListRooms([], "some_user")
        ep = p.encode()
        dp = decode(ep)
        self.assertEqual(p, dp)

    def test_ListRooms_withRooms(self):
        p = ListRooms(["first", "second", "third"], "some_user")
        ep = p.encode()
        dp = decode(ep)
        self.assertEqual(p, dp)

    def test_MessageRoom(self):
        p = MessageRoom("room", "message", "user")
        ep = p.encode()
        dp = decode(ep)
        self.assertEqual(p, dp)

    def test_ListUsers_empty(self):
        p = ListUsers([], "user")
        ep = p.encode()
        dp = decode(ep)
        self.assertEqual(p, dp)

    def test_ListUsers_withUsers(self):
        p = ListUsers(["some user", "another user", "a third user"], "user")
        ep = p.encode()
        dp = decode(ep)
        self.assertEqual(p, dp)

    def test_PrivateMessage(self):
        p = PrivateMessage("from", "to", "message")
        ep = p.encode()
        dp = decode(ep)
        self.assertEqual(p, dp)

    def test_Broadcast(self):
        p = Broadcast("some message", "some_user")
        ep = p.encode()
        dp = decode(ep)
        self.assertEqual(p, dp)


if __name__ == '__main__':
    unittest.main()
