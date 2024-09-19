import cave
import cave.math
import cave.random

class VehicleController(cave.Component):
	def start(self, scene):
		self.vehicle : cave.VehicleComponent = self.entity.get("Vehicle")
		self.rigidBody : cave.RigidBodyComponent = self.entity.get("Rigid Body")

		# Playing the Engine sound...
		self.sd = cave.playSound("car-engine-02.ogg", 2, -1)

		# This force variable is a way to don't instantly apply full throttle
		# to the vehicle. Instead, we slowly increate it as you hold the acc.
		self.force = 0.0
		self.brakeForce = 0.0

		self.lastSparkPos = cave.Vector3(0)
		self.lastSparkTimer = cave.SceneTimer()

	def addForce(self, value):
		self.force = cave.math.clamp(self.force + value, 0.0, 1.0)

	def addBrakeForce(self, value):
		self.brakeForce = cave.math.clamp(self.brakeForce + value, 0.0, 1.0)

	def movement(self):
		dt = cave.getDeltaTime()
		events = cave.getEvents()

		if events.active(cave.event.KEY_W):
			self.addForce(dt)
			self.vehicle.accelerate(self.force)
		elif events.active(cave.event.KEY_S):
			self.addForce(dt * 0.5)
			self.vehicle.reverse(self.force)
		else:
			self.addForce(-dt * 0.5)
			self.vehicle.idle()
		
		if events.active(cave.event.KEY_SPACE):
			self.addBrakeForce(dt * 0.2)
			print(self.brakeForce)
			self.vehicle.brake(self.brakeForce)
		else:
			self.addBrakeForce(-dt * 2)
			self.vehicle.brakeRelease()

		if events.active(cave.event.KEY_A):
			self.vehicle.turnLeft()
		elif events.active(cave.event.KEY_D):
			self.vehicle.turnRight()
		else:
			self.vehicle.turnStraight()
		
	def soundControl(self):		
		if self.sd.isPaused():
			self.sd.resume()

		self.sd.pitch  = cave.math.mapRange(self.force, 0, 1, 0.5, 1.0)
		self.sd.volume = cave.math.mapRange(self.force, 0, 1, 0.7, 2.0)

	def damageControl(self):
		scene = cave.getScene()

		for col in self.rigidBody.getCollisions():
			if col.position.length() < 0.5:
				continue
			if (self.lastSparkPos - col.position).length() < 2.0 and self.lastSparkTimer.get() < 1.0:
				continue
			
			# Collision Effect:
			spark = scene.addFromTemplate("Spark", col.position)
			spark.scheduleKill(0.5)

			# Collision Sound:
			sd = cave.playSound("crash-01.ogg", 0.5)
			sd.setSource3D(spark)
			sd.pitch = cave.random.uniform(0.5, 2.0)

			self.lastSparkPos = col.position.copy()
			self.lastSparkTimer.reset()
			break

	def update(self):
		self.movement()
		self.soundControl()

		self.damageControl()
		
	def pausedUpdate(self):
		if self.sd.isPlaying():
			self.sd.pause()

	def end(self, scene):
		pass
	


