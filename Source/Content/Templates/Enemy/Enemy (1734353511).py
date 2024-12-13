import cave


class Enemy(cave.Component):
	def start(self, scene: cave.Scene):
		self.scene = scene

		self.mesh = self.entity.getChild("Proto Mesh")
		self.transf = self.entity.getTransform()
		self.meshTransf = self.mesh.getTransform()
		self.character : cave.CharacterComponent = self.entity.get("Character")
		self.animator  : cave.AnimationComponent = self.mesh.get("Animation")

		self.isRunning = False
		self.spawnPoint = self.transf.worldPosition.copy()

		self.fsm = cave.StateMachine(self)
		self.fsm.setState(EStatePatrol())

	def canMoveForward(self) -> bool:
		fwd = self.meshTransf.getForwardVector() * 0.2
		pos = self.transf.worldPosition + cave.Vector3(0, 1, 0)

		mask = cave.BitMask(False)
		mask.enable(0)
		
		if self.scene.rayCast(pos, pos + fwd, mask).hit:
			return False
		return self.scene.rayCast(pos + fwd, pos + fwd - cave.Vector3(0,2,0), mask).hit

	def updateAnimation(self):
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
		self.fsm.run()
		self.updateAnimation()
		
	def end(self, scene: cave.Scene):
		pass
	