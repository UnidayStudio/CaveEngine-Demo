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

		self.isRunning = False

	def isAttacking(self) -> bool:
		layer : cave.AnimationComponentAnimationLayer = self.animator.getAnimation(0)
		if layer is None:
			return False
		return layer.priority > 0
	
	def movement(self):
		dt = cave.getDeltaTime()
		events = cave.getEvents()

		x, z = 0, 0
		if not self.isAttacking():
			x = events.active(cave.event.KEY_A) - events.active(cave.event.KEY_D)
			z = events.active(cave.event.KEY_W) - events.active(cave.event.KEY_S)

			self.isRunning = events.active(cave.event.KEY_LSHIFT)
			
			if events.pressed(cave.event.KEY_SPACE):
				self.character.jump()

			if self.character.onGround():
				if events.pressed(cave.event.MOUSE_LEFT):
					options = ["p-atk-kick", "p-atk-punch-1", "p-atk-punch-2", "p-atk-punch-3"]
					hndl = self.animator.playByName(options[cave.random.randint(0, len(options) - 1)], 0.2, priority=1)
					hndl.speed *= 1.2

		dir = cave.Vector3(x, 0, z) 
		if dir.length() > 0.0:
			dir.normalize()
		dir *= self.runSpeed if self.isRunning else self.walkSpeed
		self.character.setWalkDirection(dir * dt)

	def animation(self):
		dir = self.character.getWalkDirection()

		if dir.length() > 0.0:
			self.meshTransf.lookAtSmooth(-dir, 0.2 if self.character.onGround() else 0.06)

		if self.character.onGround():
			if dir.length() > 0.0:
				if self.isRunning:
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

		# This is necessary to avoid the attack animation to stop immediately:
		layer : cave.AnimationComponentAnimationLayer = self.animator.getAnimation(0)
		if layer:
			if layer.priority > 0:
				if layer.getProgress() > 0.8:
					layer.priority = 0
					self.animator.playByName("p-idle", 0.2, loop=True)

	def update(self):
		self.movement()
		self.animation()
		
	def end(self, scene: cave.Scene):
		pass
	