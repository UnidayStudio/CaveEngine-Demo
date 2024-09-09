import cave

class VehicleController(cave.Component):
	def start(self, scene):
		self.vehicle = self.entity.get("Vehicle")

	def update(self):
		events = cave.getEvents()

		if events.active(cave.event.KEY_W):
			self.vehicle.accelerate()
		elif events.active(cave.event.KEY_S):
			self.vehicle.reverse()
		else:
			self.vehicle.idle()

		if events.pressed(cave.event.KEY_LCTRL):
			self.vehicle.brake()
		elif events.released(cave.event.KEY_LCTRL):
			self.vehicle.brakeRelease()

		if events.active(cave.event.KEY_A):
			self.vehicle.turnLeft()
		elif events.active(cave.event.KEY_D):
			self.vehicle.turnRight()
		else:
			self.vehicle.turnStraight()
		
	def end(self, scene):
		pass
	

