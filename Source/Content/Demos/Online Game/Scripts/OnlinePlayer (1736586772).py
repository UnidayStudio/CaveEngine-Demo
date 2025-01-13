import cave
import cave.math

class OnlinePlayer(cave.Component):
	walkSpeed = 5.0
	runSpeed = 8.0

	def start(self, scene: cave.Scene):
		self.transf = self.entity.getTransform()
		self.character : cave.CharacterComponent = self.entity.get("Character")

		self.camera : cave.CameraComponent = self.entity.getChild("Camera").get("Camera")
		self.camera.useCamera = False

		self.mesh = self.entity.getChild("Proto Mesh")
		self.meshTransf = self.mesh.getTransform()
		self.animator : cave.AnimationComponent = self.mesh.get("Animation")

		# Since we won't have the Character's walkDirection for the online clients,
		# we will have to manually keep track of the movement with this variable:
		self.lastPos = self.transf.getWorldPosition()
			
	def updateControls(self):
		dt = cave.getDeltaTime()
		events = cave.getEvents()

		x = events.active(cave.event.KEY_A) - events.active(cave.event.KEY_D)
		z = events.active(cave.event.KEY_W) - events.active(cave.event.KEY_S)

		isRunning = events.active(cave.event.KEY_LSHIFT)
		
		if events.pressed(cave.event.KEY_SPACE):
			self.character.jump()

		dir = cave.Vector3(x, 0, z) 

		if dir.length() > 0.0:
			# Normalizing the walk dir to avoid it moving faster diagonally:
			dir.normalize()

		# Move speed is based if the player is running or not:
		dir *= self.runSpeed if isRunning else self.walkSpeed
		self.character.setWalkDirection(dir * dt)

	def updateAnimations(self):
		dt = cave.getDeltaTime()
		
		pos = self.transf.getWorldPosition()
		dir = (pos - self.lastPos) / dt
		self.lastPos = pos.copy()

		if dir.length() > 0.0:
			# Making the character mesh look at the aiming direction:
			self.meshTransf.lookAtSmooth(-dir, 0.2 if self.character.onGround() else 0.06)

		if self.character.onGround():
			if dir.length() > self.walkSpeed * 0.5:
				if dir.length() > cave.math.lerp(self.walkSpeed, self.runSpeed, 0.5):
					self.animator.playByName("p-run", 0.2, loop=True)
				else:
					self.animator.playByName("p-walk", 0.2, loop=True)
			else:
				self.animator.playByName("p-idle", 0.2, loop=True)
		else:
			if self.character.isFalling():
				self.animator.playByName("p-fall-1", 0.4, loop=True)
			else:
				self.animator.playByName("p-fall-2", 0.3, loop=True)

	def update(self):
		hasControl = self.entity.properties.get("hasControl", False)

		self.camera.useCamera = hasControl
		if hasControl:
			self.updateControls()
			
		self.updateAnimations()
		
	def end(self, scene: cave.Scene):
		pass
	