import time, random, datetime
from Houdini.Handlers import Handlers, XT
from Houdini.Data.Mail import Mail
from Houdini.Data.Penguin import Penguin

@Handlers.Handle(XT.StartMailEngine)
def handleStartMailEngine(self, data):
    if not self.agentStatus and random.random() < 0.4:
        q = self.session.query(Mail).filter(Mail.Recipient == self.user.ID).\
            filter((Mail.Type == '112') | (Mail.Type == '47'))
        epfInvited = self.session.query(q.exists()).scalar()
        if not epfInvited:
            postcard = Mail(Recipient=self.user.ID, SenderName="sys",
                            SenderID=0, Details="", Date=int(time.time()),
                            Type=112)
            self.session.add(postcard)

    lastPaycheck = self.user.LastPaycheck;
    if lastPaycheck == 0:
        lastPaycheck = datetime.datetime.now()
    else:
        lastPaycheck = datetime.datetime.fromtimestamp(lastPaycheck)
    today = datetime.datetime.now()
    lastPaycheck = lastPaycheck.replace(month=(lastPaycheck.month + 1))
    lastPaycheck = lastPaycheck.replace(day=2)
    while lastPaycheck < today:
        paycheckDate = int(time.mktime(lastPaycheck.timetuple()))
        if 428 in self.inventory:
            postcard = Mail(Recipient=self.user.ID, SenderName="sys",
                            SenderID=0, Details="", Date=paycheckDate,
                            Type=172)
            self.session.add(postcard)
            self.user.Coins += 250
        if self.agentStatus:
            postcard = Mail(Recipient=self.user.ID, SenderName="sys",
                            SenderID=0, Details="", Date=paycheckDate,
                            Type=171)
            self.session.add(postcard)
            self.user.Coins += 250

        lastPaycheck = lastPaycheck.replace(month=(lastPaycheck.month + 1))
        lastPaycheck = lastPaycheck.replace(day=2)
    self.user.LastPaycheck = int(time.mktime(today.timetuple()))
    self.session.commit()

    totalMail = self.session.query(Mail).\
        filter(Mail.Recipient == self.user.ID).count()
    unreadMail = self.session.query(Mail).\
        filter(Mail.Recipient == self.user.ID).\
        filter(Mail.HasRead == False).count()

    self.sendXt("mst", unreadMail, totalMail)

@Handlers.Handle(XT.GetMail)
def handleGetMail(self, data):
    mailbox = self.session.query(Mail).\
        filter(Mail.Recipient == self.user.ID)
    postcardArray = []
    for postcard in mailbox:
        postcardArray.append("|".join([postcard.SenderName, str(postcard.SenderID),
                                       str(postcard.Type), postcard.Details, str(postcard.Date),
                                       str(postcard.ID), str(int(postcard.HasRead))]))
    postcardString = "%".join(postcardArray)
    self.sendXt("mg", postcardString)

@Handlers.Handle(XT.SendMail)
def handleSendMail(self, data):
    q = self.session.query(Penguin).filter(Penguin.ID == data.RecipientId)
    recipientExists = self.session.query(q.exists()).scalar()
    if not recipientExists:
        return
    if self.user.Coins < 10:
        self.sendXt("ms", self.user.Coins, 2)
        self.logger.debug("%d tried to send postcard with insufficient funds.", self.user.ID)
        return
    recipientMailCount = self.session.query(Mail).\
        filter(Mail.Recipient == data.RecipientId).count()
    if recipientMailCount >= 100:
        self.sendXt("ms", self.user.Coins, 0)
    self.user.Coins -= 10
    currentTimestamp = int(time.time())
    postcard = Mail(Recipient=data.RecipientId, SenderName=self.user.Username,
           SenderID=self.user.ID, Details="", Date=currentTimestamp,
           Type=data.PostcardId)
    self.session.add(postcard)
    self.session.commit()
    self.sendXt("ms", self.user.Coins, 1)
    if data.RecipientId in self.server.players:
        recipientObject = self.server.players[data.RecipientId]
        recipientObject.sendXt("mr", self.user.Username, self.user.ID, data.PostcardId,
                               "", currentTimestamp, postcard.ID)
    self.logger.info("%d send %d a postcard (%d).", self.user.ID, data.RecipientId,
                     data.PostcardId)

@Handlers.Handle(XT.MailChecked)
def handleMailChecked(self, data):
    self.session.query(Mail).\
        filter(Mail.Recipient == self.user.ID).\
        update({"HasRead": True})
    self.session.commit()

@Handlers.Handle(XT.DeleteMail)
def handleDeleteMail(self, data):
    self.session.query(Mail).\
        filter(Mail.Recipient == self.user.ID).\
        filter(Mail.ID == data.PostcardId).delete()
    self.session.commit()

@Handlers.Handle(XT.DeleteMailFromUser)
def handleDeleteMailFromUser(self, data):
    self.session.query(Mail).\
        filter(Mail.Recipient == self.user.ID).\
        filter(Mail.SenderID == data.SenderId).delete()
    self.session.commit()
    totalMail = self.session.query(Mail). \
        filter(Mail.Recipient == self.user.ID).count()
    self.sendXt("mdp", totalMail)