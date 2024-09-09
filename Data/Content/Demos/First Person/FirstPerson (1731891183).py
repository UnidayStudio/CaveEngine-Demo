import cave

class FirstPersonController(cave.Component):
	walkSpeed = 5.0
	runSpeed = 8.0

	def start(self, scene: cave.Scene):
		self.transf = self.entity.getTransform()
		self.character : cave.CharacterComponent = self.entity.get("Character")

		self.cam = self.entity.getChild("Camera")
		self.camTransf = self.cam.getTransform()

	def movement(self):
		dt = cave.getDeltaTime()
		events = cave.getEvents()

		x = events.active(cave.event.KEY_A) - events.active(cave.event.KEY_D)
		z = events.active(cave.event.KEY_W) - events.active(cave.event.KEY_S)

		dir = cave.Vector3(x, 0, z) 
		if dir.length() > 0.0:
			dir.normalize()
		self.character.setWalkDirection(dir * self.walkSpeed * dt)

		if events.pressed(cave.event.KEY_SPACE):
			self.character.jump()

	def mouselook(self, sens=-0.006):
		events = cave.getEvents()
		events.setRelativeMouse(True)

		motion = events.getMouseMotion() * sens

		self.transf.rotateOnYaw(motion.x)
		self.camTransf.rotateOnPitch(motion.y)

	def update(self):
		self.movement()
		self.mouselook()
		
	def end(self, scene: cave.Scene):
		pass
	