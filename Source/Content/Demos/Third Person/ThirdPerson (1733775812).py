import cave
import cave.math

class ThirdPersonController(cave.Component):
	walkSpeed = 5.0
	runSpeed = 8.0

	debugIk = False

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

		self.footIkBlend = {
			"mixamorig:LeftFoot"  : 1.0,
			"mixamorig:RightFoot" : 1.0,
		}
		self.fookIkHipsOffset = 0.0

	def calculateFootIk(self, boneName: str):
		dt = cave.getDeltaTime()

		self.footIkBlend[boneName] += dt if self.character.onGround() else -dt
		self.footIkBlend[boneName] = cave.math.clamp(self.footIkBlend[boneName], 0.0, 1.0)

		arm : cave.Armature = self.animator.armature.get()
		bone = arm.getBone(boneName)

		# Bone Transforms are local to the Armature transform, so we
		# need to manually move the transformation back and forth.
		worldPos = self.meshTransf.transformVector(bone.getWorldPosition())

		# I'm using the animation's Y position of the foot to blend out
		# the IK, because when the character raises his leg, of course we
		# no longer wants to apply the technique. In this specific character
		# and set of animations, the feet is "on ground" when ti's around 
		# the value of 0.14 on the Y axis. You can test this in yours by
		# simply printing this height value to the console while idling.
		height = bone.getWorldPosition().y

		blend = cave.math.mapRange(height, 0.14, 0.22, 0.0, 1.0)
		blend = 1.0 - cave.math.clamp(blend, 0.0, 1.0)
		blend = self.footIkBlend[boneName] * blend

		# Raycasting the Ground, from the Feet position:
		res = self.entity.getScene().rayCast(
			worldPos + cave.Vector3(0, 0.5, 0), 
			worldPos - cave.Vector3(0, 0.5, 0)
		)
		pos = None

		# If it finds a ground, align the Foot with IK:
		if res.hit:
			# I'm adding 0.1 here to compensate for the Feet thickness.
			pos = self.meshTransf.untransformVector(res.position) + cave.Vector3(0, 0.1, 0)

		return bone, pos, blend
	
	def applyFootIk(self):
		# I'm not immediately applying the Foot IK because I also need to calculate
		# an offset to apply to the Hips, so the entire character can move a bit up
		# or down do compensate if the terrain is too steep and one of the legs needs
		# to be way down. If we don't compensate for that, one leg will be floating
		# most of the times.
		boneL, posL, blendL = self.calculateFootIk("mixamorig:LeftFoot")
		boneR, posR, blendR = self.calculateFootIk("mixamorig:RightFoot")

		offsetY = 0.0
		if posL: offsetY = min(offsetY, (posL.y - boneL.getWorldPosition().y) * blendL)
		if posR: offsetY = min(offsetY, (posR.y - boneR.getWorldPosition().y) * blendR)

		self.fookIkHipsOffset = cave.math.lerp(self.fookIkHipsOffset, offsetY, 0.1)

		arm : cave.Armature = self.animator.armature.get()
		hips = arm.getBone("mixamorig:Hips")

		before = self.meshTransf.transformVector(hips.getWorldPosition())

		# I'm compensating for the Height Change...
		hips.setWorldPosition(hips.getWorldPosition() + cave.Vector3(0, self.fookIkHipsOffset, 0))

		after = self.meshTransf.transformVector(hips.getWorldPosition())

		if self.debugIk and cave.hasEditor():
			scene = cave.getScene()

			scene.addDebugArrow(before, after, cave.Vector3(1,0,0))
			scene.addDebugSphere(self.meshTransf.getWorldPosition(), 0.2, cave.Vector3(0,1,0))
			
			if posL: scene.addDebugSphere(posL, 0.1, cave.Vector3(1,0,0))
			if posR: scene.addDebugSphere(posR, 0.1, cave.Vector3(1,0,0))

		# Finally, let's apply the IK when necessary:
		if posL: boneL.inverseKinematics(posL, 2, blendL)
		if posR: boneR.inverseKinematics(posR, 2, blendR)

	def postEvaluate(self):
		"""
		In this callback, if the player is aiming, we want to align the Spine Bone
		of the armature to the camera view direction, so let's do it here:
		"""

		weight = self.animator.getLayerWeight(1)
		if self.isAiming or weight > 0:
			arm : cave.Armature = self.animator.armature.get()
			bSpine = arm.getBone("mixamorig:Spine")
			bSpine.lookAtSmooth(self.camTransf.getForwardVector(), weight, cave.Vector3(-0.1, 1, 0))
			bSpine.rotateOnYaw(-0.7 * weight)

		# IK for the Foot Placement:
		self.applyFootIk()

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
	