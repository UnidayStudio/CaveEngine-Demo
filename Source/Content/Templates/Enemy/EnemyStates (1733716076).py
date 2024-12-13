import cave
import cave.math
import cave.random
import cave.random


ENEMY_MIN_DISTANCE = 1.0

class EStatePatrol(cave.State):
	class Idle(cave.State):
		def start(self):
			self.timer = cave.SceneTimer()

		def update(self):
			self.component.character.setWalkDirection(0, 0, 0)

			if self.timer.get() > 1.0:
				if cave.random.random() < 0.5:
					return EStatePatrol.Walk()
				self.timer.reset()

	class Walk(cave.State):
		def start(self):
			angle  = cave.random.uniform(0, 6.3)
			radius = cave.random.uniform(0, self.entity.properties.get("patrolRange", 1.0))

			self.target = cave.Vector3(0)
			for _ in range(16):
				self.target = self.component.spawnPoint.copy()
				self.target += cave.Vector3(cave.math.sin(angle), 0, cave.math.cos(angle)) * radius

				if (self.target - self.component.transf.worldPosition).length() < ENEMY_MIN_DISTANCE * 2:
					break
			
		def update(self):
			dt = cave.getDeltaTime()

			dir = (self.component.transf.worldPosition - self.target)
			dir.y = 0
			
			self.component.isRunning = False
			self.component.transf.lookAtSmooth(dir.normalized(), 0.1)
			self.component.character.setWalkDirection(0, 0, self.entity.properties.get("walkSpeed", 1.0) * dt)

			if dir.length() <= ENEMY_MIN_DISTANCE or not self.component.canMoveForward():
				return EStatePatrol.Idle()

	def start(self):
		self.fsm = cave.StateMachine(self.component)
		options = [EStatePatrol.Idle, EStatePatrol.Walk]
		self.fsm.setState(options[cave.random.randint(0, len(options) - 1)]())

	def update(self):
		self.fsm.run()


class EStateCombat(cave.State):
	pass
