import cave

class FirstPersonController(cave.Component):
	walkSpeed = 5.0
	runSpeed = 8.0

	def start(self, scene: cave.Scene):
		self.transf = self.entity.getTransform()
		self.character : cave.CharacterComponent = self.entity.get("Character")

		self.cam = self.entity.getChild("Camera")
		self.camTransf = self.cam.getTransform()

		# This will control the fire rate...
		self.shotTimer = cave.SceneTimer()

		self.muzzle = self.entity.getChild("Muzzle")
		self.mesh = self.entity.getChild("FPS Mesh")
		self.animator : cave.AnimationComponent = self.mesh.get("Animation")

		self.movementState = 0 # [idle, walking, running]
		self.movementTimer = cave.SceneTimer() # To add footsteps...

	def movement(self):
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

	def mouselook(self, sens=-0.006):
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

	def shoot(self):
		events = cave.getEvents()
		scene = cave.getScene()
		cam = scene.getCamera()

		# If the Player is holding the Left Mouse Button, it should be able to shoot.
		# But I'm also using a timer to limit how many bullets per second it will be
		# able to shoot. Otherwise, it will become a mess!
		if events.active(cave.event.MOUSE_LEFT) and self.shotTimer.get() > 0.1:
			self.shotTimer.reset()

			# Shot Sound:
			sd = cave.playSound("bang-04.ogg")
			sd.pitch = cave.random.uniform(0.4, 1.0)

			# Duplicating the Muzzle Effect...
			muzzle = scene.copyEntity(self.muzzle)
			muzzle.activate(scene)
			muzzle.scheduleKill(0.05) # Only lasts for a fraction of a Second

			# I'll raycast from the camera position to its backward direction 
			# in order to see if the projectile hits something. 
			origin = cam.getWorldPosition()
			target = origin + cam.getForwardVector(True) * -1000

			# I'll also create a Mask so the raycast only checks for the bodies
			# with the 7th bit enabled. This will prevent it from hitting the
			# player capsule itself.
			mask = cave.BitMask(False)
			mask.enable(7)

			# Then I raycast and check to see if it hits...
			result = scene.rayCast(origin, target, mask)
			if result.hit:
				# Adding the Bullet Hole based on its Entity Template:
				obj = scene.addFromTemplate("Bullet Hole", result.position)
				obj.getTransform().lookAt(result.normal)

				# Schedule the bullet hole to be killed after 5 seconds...
				obj.scheduleKill(5.0)

	def animateAndSounds(self):
		layer : cave.AnimationComponentAnimationLayer = self.animator.getAnimation(0)
		layer.speed = 100

		addFootstep = False
		timer = self.movementTimer.get()

		if self.movementState == 1:
			if timer > 0.3:
				addFootstep = True
			layer.speed = 300
		elif self.movementState == 2:
			if timer > 0.22:
				addFootstep = True
			layer.speed = 500

		if addFootstep and self.character.onGround():
			self.movementTimer.reset()

			sd = cave.playSound("footstep-1.ogg")
			sd.pitch = cave.random.uniform(0.5, 1.5)
			sd.volume = 0.2

	def update(self):
		self.movement()
		self.mouselook()
		self.shoot()
		self.animateAndSounds()
		
	def end(self, scene: cave.Scene):
		pass
	
