from Spheniscidae import Spheniscidae
from Data.Puffle import Puffle

class Penguin(Spheniscidae):

	def __init__(self, session, spirit):
		super(Penguin, self).__init__(session, spirit)

		# Defined in handleLogin if authentication is successful
		self.user = None

		self.frame = 1
		self.x, self.y = (0, 0)

		self.playerString = None
		self.buddies = {}
		self.puffles = {}
		self.ignore = {}

		self.logger.info("Penguin class instantiated")

	def addItem(self, itemId, itemCost=0):
		if itemId in self.inventory:
			return False

		self.inventory.append(itemId)

		stringifiedInventory = map(str, self.inventory)
		self.user.Inventory = "%".join(stringifiedInventory)

		self.user.Coins -= itemCost

		self.sendXt("ai", itemId, self.user.Coins)

	""" TODO: Ensure valid stamp ID's (probably do this
	when we implement the mini-game end screen stamp 
	overviews
	"""
	def addStamp(self, stampId, sendXt=False):
		stamps = self.user.Stamps.split("|")
		if stampId in stamps:
			return False

		# Check if the first element is an empty string, if so remove
		if not stamps[0]:
			del stamps[0]

		recentStamps = self.user.RecentStamps.split("|")
		stamps.append(stampId)
		recentStamps.append(stampId)
		stringifiedStamps = map(str, stamps)
		stringifiedRecentStamps = map(str, recentStamps)
		self.user.Stamps = "|".join(stringifiedStamps)
		self.user.RecentStamps = "|".join(stringifiedRecentStamps)
		self.session.commit()
		if sendXt:
			self.sendXt("aabs", stampId)

	# TODO: Puffle values
	def getPlayerString(self):
		"""TODO: Make this work properly
		if self.playerString is not None:
			return self.playerString
		"""

		playerArray = (
			self.user.ID,
			self.user.Username,
			1,
			self.user.Color,
			self.user.Head,
			self.user.Face,
			self.user.Neck,
			self.user.Body,
			self.user.Hand,
			self.user.Feet,
			self.user.Flag,
			self.user.Photo,
			self.x,
			self.y,
			self.frame,
			1,
			1, # Membership days
		)

		playerStringArray = map(str, playerArray)
		self.playerString = "|".join(playerStringArray)

		return self.playerString

	def connectionLost(self, reason):
		# This indicates that the client was successfully authorized
		# and joined the server w/ all their stuff loaded
		if hasattr(self, "room") and self.room is not None:
			self.room.remove(self)

			# Stop walking any puffles
			puffleId = self.session.query(Puffle.ID) \
				.filter(Puffle.Owner == self.user.ID, Puffle.Walking == 1)

			if puffleId is not None:
				self.user.Hand = 0
				self.session.query(Puffle.ID == puffleId).update({"Walking": 0})

			# Let buddies know that they've logged off
			for buddyId in self.buddies.keys():
				if buddyId in self.server.players:
					self.server.players[buddyId].sendXt("bof", self.user.ID)

			# Remove them from Redis
			self.server.redis.srem("%s.players" % self.server.serverName, self.user.ID)
			self.server.redis.decr("%s.population" % self.server.serverName)

		super(Penguin, self).connectionLost(reason)