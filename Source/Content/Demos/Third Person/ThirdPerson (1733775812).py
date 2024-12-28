import cave

class ThirdPersonController(cave.Component):
	walkSpeed = 5.0
	runSpeed = 8.0

	def start(self, scene: cave.Scene):
		self.transf = self.entity.getTransform()
		self.character : cave.CharacterComponent = self.entity.get("Character")

		self.mesh = self.entity.getChild("Proto Mesh")
		self.meshTransf = self.mesh.getTransform()
		self.animator : cave.AnimationComponent = self.mesh.get("Animation")

		self.cam = self.entity.getChild("Camera")
		self.camTransf = self.cam.getTransform()
		self.camCmp : cave.ThirdPersonCamComponent = self.cam.get("ThirdPersonCam")

		self.isRunning = False
		self.isAiming  = False
		self.inputDir = cave.Vector3(0)
		
		# Now we will create an Animation Layer Filter to the Animator
		# . for us to be able to play the Axe animation on Layer 1 (which is
		# . the second anim layer, after layer 0) but only influence the upper
		# . Bones of the Armature and not mess with the legs!
		filter = self.animator.createLayerFilter(1)
		arm : cave.Armature = self.animator.armature.get()
		bSpine = arm.getBone("mixamorig:Spine")
		filter.setToBone(bSpine, 1.0, True)

		# We will assign a callback for the armature:
		self.animator.addPostEvaluationCallback(self.postEvaluate)

	def postEvaluate(self):
		"""
		In this callback, if the player is aiming, we want to align the Spine Bone
		of the armature to the camera view direction, so let's do it here:
		"""

		if self.isAiming:
			arm : cave.Armature = self.animator.armature.get()
			bSpine = arm.getBone("mixamorig:Spine")
			bSpine.lookAt(self.camTransf.getForwardVector(), cave.Vector3(-0.1, 1, 0))
			bSpine.rotateOnYaw(-0.7)

	def isAttacking(self) -> bool:
		"""
		This method will check, based on the currently being player anim, if the
		player is attacking (returns True) or not (returns False).
		"""
		layer : cave.AnimationComponentAnimationLayer = self.animator.getAnimation(0)
		if layer is None:
			return False
		return layer.priority > 0
	
	def updateControls(self):
		"""
		This method will evaluate all the player's mouse and keyboard inputs and
		perform the appropriate behaviors such as move around (walk or run), jump,
		aim, attack, etc.
		"""

		dt = cave.getDeltaTime()
		events = cave.getEvents()

		self.isAiming = False

		x, z = 0, 0
		if not self.isAttacking():
			x = events.active(cave.event.KEY_A) - events.active(cave.event.KEY_D)
			z = events.active(cave.event.KEY_W) - events.active(cave.event.KEY_S)

			self.isAiming  = events.active(cave.event.MOUSE_RIGHT) and self.character.onGround()
			self.isRunning = events.active(cave.event.KEY_LSHIFT) and not self.isAiming
			
			if events.pressed(cave.event.KEY_SPACE) and not self.isAiming:
				self.character.jump()

			# Only attack if the character is on ground + press Left Mouse Button:
			if self.character.onGround() and events.pressed(cave.event.MOUSE_LEFT):
				options = ["p-atk-kick", "p-atk-punch-1", "p-atk-punch-2", "p-atk-punch-3"]
				hndl = self.animator.playByName(options[cave.random.randint(0, len(options) - 1)], 0.2, priority=1)
				hndl.speed *= 1.2

		self.inputDir = cave.Vector3(x, 0, z)
		dir = cave.Vector3(x, 0, z) 

		if dir.length() > 0.0:
			# Normalizing the walk dir to avoid it moving faster diagonally:
			dir.normalize()

		# Move speed is based if the player is running or not:
		dir *= self.runSpeed if self.isRunning else self.walkSpeed
		self.character.setWalkDirection(dir * dt)

	def updateAnimations(self):
		"""
		This method will get all the state previously set by the updateControls
		and based on that, will execute the most appropriate Animations such as
		idle, walk, run, fall, etc.
		"""

		# dir will represent the walk direction, but the character mesh itself 
		# may be looking at a different direction, for example, when the player
		#  is aiming. So we will handle those separately:
		dir = self.character.getWalkDirection()
		aimDir = dir.copy()

		if self.isAiming:
			aimDir = self.transf.getForwardVector()
			self.camCmp.alignPlayer = cave.ThirdPersonCamComponentAlignPlayerRule.ALWAYS
		else:
			self.camCmp.alignPlayer = cave.ThirdPersonCamComponentAlignPlayerRule.ON_MOVEMENT

		if aimDir.length() > 0.0:
			# Making the character mesh look at the aiming direction:
			self.meshTransf.lookAtSmooth(-aimDir, 0.2 if self.character.onGround() else 0.06)

		# We need to adjust the layer 1 weight, which is the layer that we play
		# the "combat" (idle-axe) animation on top and it only affects the upper
		# bones, not the legs. We only want this to be true at all IF the player
		# is currently aiming. Otherwise, we fade it down.
		layerWeight = self.animator.getLayerWeight(1)
		layerWeight = cave.math.lerp(layerWeight, 1.0 if self.isAiming else 0.0, 0.1)
		self.animator.setLayerWeight(1, layerWeight)

		# Playing the layer 1 animation:
		self.animator.playByName("p-idle-axe", loop=True, layer=1)

		if self.character.onGround():
			if dir.length() > 0.0:
				if self.isRunning:
					self.animator.playByName("p-run", 0.2, loop=True)
				elif self.isAiming:
					keyW = self.inputDir.z > 0
					keyS = self.inputDir.z < 0
					keyA = self.inputDir.x > 0
					keyD = self.inputDir.x < 0

					if keyW and keyA:
						self.animator.playByName("p-walk-forward-left", 0.2, loop=True)
					elif keyW and keyD:
						self.animator.playByName("p-walk-forward-right", 0.2, loop=True)
					elif keyS and keyA:
						self.animator.playByName("p-walk-back-left", 0.2, loop=True)
					elif keyS and keyD:
						self.animator.playByName("p-walk-back-right", 0.2, loop=True)
					
					elif keyW:
						self.animator.playByName("p-walk", 0.2, loop=True)
					elif keyS:
						self.animator.playByName("p-walk-back", 0.2, loop=True)					
					elif keyA:
						self.animator.playByName("p-walk-left-2", 0.2, loop=True)
					elif keyD:
						self.animator.playByName("p-walk-right-2", 0.2, loop=True)
				else:
					self.animator.playByName("p-walk", 0.2, loop=True)
			else:
				self.animator.playByName("p-idle", 0.2, loop=True)
		else:
			if self.character.isFalling():
				self.animator.playByName("p-fall-1", 0.4, loop=True)
			else:
				self.animator.playByName("p-fall-2", 0.3, loop=True)

		# This is necessary to avoid the attack animation to stop immediately:
		layer : cave.AnimationComponentAnimationLayer = self.animator.getAnimation(0)
		if layer:
			if layer.priority > 0:
				if layer.getProgress() > 0.8:
					layer.priority = 0
					self.animator.playByName("p-idle", 0.2, loop=True)

	def update(self):
		self.updateControls()
		self.updateAnimations()
		
	def end(self, scene: cave.Scene):
		pass
	