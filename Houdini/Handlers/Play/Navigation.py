import time, random
from datetime import date

from Houdini.Handlers import Handlers, XT
from Houdini.Room import Room

@Handlers.Handle(XT.JoinWorld)
def handleJoinWorld(self, data):
    if int(data.ID) != self.user.ID:
        return self.transport.loseConnection()

    if data.LoginKey == "":
        return self.transport.loseConnection()

    if data.LoginKey != self.user.LoginKey:
        self.user.LoginKey = ""
        return self.sendErrorAndDisconnect(101)

    self.agentStatus, self.fieldOpStatus, \
        self.careerPoints, self.agentPoints = map(int, self.user.EPF.split(","))

    self.sendXt("js", 1, self.agentStatus, self.user.Moderator, 1)

    # Casting to integer floor's and removes the decimal
    currentTime = int(time.time())
    penguinStandardTime = currentTime * 1000
    serverTimeOffset = 7

    registrationDate = date.fromtimestamp(self.user.RegistrationDate)
    currentDateTime = date.fromtimestamp(currentTime)

    self.age = (currentDateTime - registrationDate).days

    self.sendXt("lp", self.getPlayerString(), self.user.Coins, 0, 1440,
                penguinStandardTime, self.age, 0, self.age, None, serverTimeOffset)

    self.sendXt("gps", self.user.ID, self.user.Stamps)

    self.user.LoginKey = ""
    self.user.LastLogin = currentTime

    self.session.commit()

    self.server.players[self.user.ID] = self

    buddyList = self.getBuddyList()

    for buddyId in buddyList.keys():
        if buddyId in self.server.players:
            self.server.players[buddyId].sendXt("bon", self.user.ID)

    randomRoomId = random.choice(self.server.spawnRooms)
    self.server.rooms[randomRoomId].add(self)

@Handlers.Handle(XT.JoinRoom)
def handleJoinRoom(self, data):
    if data.RoomId in self.server.rooms:
        self.x = data.X
        self.y = data.Y
        self.frame = 1

        self.room.remove(self)
        self.server.rooms[data.RoomId].add(self)

@Handlers.Handle(XT.RefreshRoom)
def handleRefreshRoom(self, data):
    self.room.refresh(self)

# TODO: Check if igloo is open or belongs to a buddy
@Handlers.Handle(XT.JoinPlayerIgloo)
def handleJoinPlayerIgloo(self, data):
    if data.Id < 1000:
        return self.transport.loseConnection()

    if data.Id not in self.server.rooms:
        igloo = self.server.rooms[data.Id] = Room(data.Id, data.Id)
        igloo.locked = True
    else:
        igloo = self.server.rooms[data.Id]

    self.room.remove(self)

    self.sendXt("jp", data.Id)
    igloo.add(self)