import cave
import cave.math
import cave.network

class OnlineServer(cave.Component):
	def start(self, scene: cave.Scene):
		self.transf = self.entity.getTransform()

		scene.paused = True
		scene.get("Lobby UI").activate(scene)
		self.gameText : cave.UIElementComponent = scene.get("GameText").get("UI Element")

		self.initialized = False

		# The Main player (controllable in this Game Instance):
		self.player = scene.addFromTemplate("Online Player", self.transf.worldPosition)
		self.player.properties["hasControl"] = True
		self.player.properties["addr"] = "" # Local
		self.player.properties["lastUpdated"] = cave.SceneTimer()

		# The other players, mapped by address:
		self.opponents = {}

		self.server : cave.network.Server = None
		self.client : cave.network.Client = None

	def isServer(self) -> bool:
		return self.entity.getScene().properties.get("server", False)

	def initialize(self):
		scene = self.entity.getScene()
		scene.get("Game UI").activate(scene)

		if self.isServer():
			self.server = cave.network.Server()
		else:
			self.client = cave.network.Client()

	def update(self):
		if not self.initialized:
			self.initialize()
			self.initialized = True

		if self.isServer():
			self.updateServer()
		else:
			self.updateClient()

		# Lerping the Position and Rotations:		
		for ent in self.opponents.values():
			transf = ent.getTransform()

			pos = ent.properties.get("targetPos", transf.getPosition())
			rot = ent.properties.get("targetRot", 0)

			transf.setPosition(transf.getPosition().lerp(pos, 0.2))
			transf.setEuler(0, cave.math.lerp(transf.getEuler().y, rot, 0.2), 0)

		# Remove all opponents that haven't been updated in a while:
		toRemove = [addr for addr in self.opponents if self.opponents[addr].properties["lastUpdated"].get() > 5.0]
		for addr in toRemove:
			self.opponents[addr].kill()
			del self.opponents[addr]

	def getPackagePosition(self, ent: cave.Entity, id: int=0) -> cave.network.Package:
		transf  = ent.getTransform()
		transf2 = ent.getChild("Proto Mesh").getTransform()

		pkg = cave.network.Package()
		pkg.writeInt(id) # Player ID 

		pkg.writeInt(0)  # Command for Position and Rotation!
		pkg.writeVector3(transf.getPosition())
		pkg.writeFloat(transf2.getWorldEuler().y)

		return pkg
	
	def parsePackages(self, packages):
		for pkg in packages:
			addr = pkg.sender.getAddress()
			id = pkg.package.readInt()

			if id == 0:
				id = addr
			else:
				id = str(id)

			if not id in self.opponents:
				ent = self.entity.getScene().addFromTemplate("Online Player")
				ent.properties["hasControl"] = False
				ent.properties["addr"] = addr
				ent.properties["lastUpdated"] = cave.SceneTimer()
				self.opponents[id] = ent

			ent : cave.Entity = self.opponents[id]
			ent.properties["lastUpdated"].reset()

			cmd = pkg.package.readInt()

			if cmd == 0: # Position and Rotation!
				ent.properties["targetPos"] = pkg.package.readVector3()
				ent.properties["targetRot"] = pkg.package.readFloat()

	def updateServer(self):
		self.gameText.setText(f"[Server] {min(self.server.getNumClients(), len(self.opponents))} Clients Connected")

		# Parsing all Incoming messages:
		self.parsePackages(self.server.popPackages())		

		# Sending all Positions back to all peers:
		entities = [self.player] + list(self.opponents.values())
		peers = self.server.getPeers()
		for ent in entities:
			entAddr = ent.properties.get("addr", "")
			pkg = self.getPackagePosition(ent, hash(entAddr) & 0xFFFFFF)

			for peer in peers:
				if peer.getAddress() == entAddr:
					continue
				peer.send(pkg, reliable=False)

		# You MUST call this at the end of every 
		# frame for the Server to function properly:
		self.server.update()

	def updateClient(self):
		if self.client.isConnected():
			self.gameText.setText("[Client] Connected!")

			# Parsing all Incoming messages:
			packages = self.client.popPackages()
			packages = [cave.network.ServerPackage(cave.network.ServerPeer(), pkg) for pkg in packages]
			self.parsePackages(packages)

			# Sending Client Position to Server:
			pkg = self.getPackagePosition(self.player)
			self.client.send(pkg, reliable=False)
		else:
			self.gameText.setText("[Client] Connecting...")

		# You MUST call this at the end of every 
		# frame for the Client to function properly:
		self.client.update()
		
	def end(self, scene: cave.Scene):
		pass
	