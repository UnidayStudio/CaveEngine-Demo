import cave
import cave.event
import cave.math

class VoxelPlayerController(cave.Component):
	"""
	First Person Controller for the Voxel World player + hability to add/remove blocks.
	"""

	walkSpeed = 2.0
	runSpeed = 6.0

	def start(self, scene: cave.Scene):
		self.transf = self.entity.getTransform()
		self.character : cave.CharacterComponent = self.entity.get("Character")

		self.cam = self.entity.getChild("Camera")
		self.camTransf = self.cam.getTransform()

	def firstUpdate(self):
		self.spawner = self.entity.get("VoxelSpawner", True)

	def updateMovement(self):
		"""
		Handles player movement (WASD, Jump, etc)
		"""

		dt = cave.getDeltaTime()
		events = cave.getEvents()

		x = events.active(cave.event.KEY_A) - events.active(cave.event.KEY_D)
		z = events.active(cave.event.KEY_W) - events.active(cave.event.KEY_S)

		isRunning = events.active(cave.event.KEY_LSHIFT)
		self.movementState = 0

		dir = cave.Vector3(x, 0, z) 
		if dir.length() > 0.0:
			dir.normalize()

			if isRunning:
				dir *= self.runSpeed
				self.movementState = 2
			else:
				dir *= self.walkSpeed
				self.movementState = 1

		self.character.setWalkDirection(dir * dt)

		if events.pressed(cave.event.KEY_SPACE):
			self.character.jump()

	def updateMouselook(self, sens=-0.006):
		"""
		Handles the first person camera mouselook controls
		"""

		events = cave.getEvents()
		events.setRelativeMouse(True)

		motion = events.getMouseMotion() * sens

		self.transf.rotateOnYaw(motion.x)
		self.camTransf.rotateOnPitch(motion.y)
		
		# Limiting the Camera Rotation:
		self.camTransf.setEuler(
			cave.Vector3(
				cave.math.clampEulerAngle(self.camTransf.euler.x, 90, 270), 
				self.camTransf.euler.y, 
				self.camTransf.euler.z
			))

	def updateAiming(self):
		"""
		Handles aiming and adding/removing blocks
		"""

		events = cave.getEvents()
		scene = self.entity.getScene()

		origin = self.camTransf.worldPosition
		target = origin - self.camTransf.getForwardVector(True) * 1000

		mask = cave.BitMask()
		mask.disable(0)

		res = scene.rayCast(origin, target, mask)

		if res.hit:
			pos = res.position + res.normal * 0.1
			pos.x = cave.math.floor(pos.x) + 0.5
			pos.y = cave.math.floor(pos.y) + 0.5
			pos.z = cave.math.floor(pos.z) + 0.5
			
			transf = cave.Transform()
			transf.position = pos
			transf.setScale(0.5)
			
			scene.addDebugSphere(res.position, 0.1, cave.Vector3(1,0,0))
			scene.addDebugCube(transf, cave.Vector3(1,1,1))

			cmp = res.entity.get("VoxelChunk", True)

			if events.pressed(cave.event.MOUSE_LEFT):
				chunk = self.spawner.getChunk(pos)
				if chunk:
					cmp = chunk.get("VoxelChunk", True)

				if cmp:
					cmp.addBlock(res.position + res.normal * 0.1)
			elif events.pressed(cave.event.MOUSE_RIGHT):
				if cmp:
					cmp.removeBlock(res.position - res.normal * 0.1)
			
	def update(self):
		self.updateMovement()
		self.updateMouselook()

		self.updateAiming()
		
	def end(self, scene: cave.Scene):
		pass
	