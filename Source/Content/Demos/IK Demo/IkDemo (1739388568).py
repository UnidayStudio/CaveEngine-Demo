import cave

class IkDemo(cave.Component):
	def start(self, scene: cave.Scene):
		self.transf = self.entity.getTransform()
		self.animator = self.entity.get("Animation")

		# Adding the Post Evaluation Callback:
		self.animator.addPostEvaluationCallback(self.callback)

		# Getting the Entity to move the Hand:
		self.handIkTransf = scene.get("Hand IK").getTransform()
		
	def applyFootIk(self, boneName: str):
		arm : cave.Armature = self.animator.armature.get()
		bone = arm.getBone(boneName)

		# Bone Transforms are local to the Armature transform, so we
		# need to manually move the transformation back and forth.
		worldPos = self.transf.transformVector(bone.getWorldPosition())

		# Raycasting the Ground, from the Feet position:
		res = self.entity.getScene().rayCast(
			worldPos + cave.Vector3(0, 0.5, 0), 
			worldPos - cave.Vector3(0, 0.1, 0)
		)

		# If it finds a ground, align the Foot with IK:
		if res.hit:
			pos = self.transf.untransformVector(res.position) + cave.Vector3(0, 0.1, 0)
			bone.inverseKinematics(pos, 2)
					
	def callback(self):
		# IK for the Foot Placement:
		self.applyFootIk("mixamorig:LeftFoot")
		self.applyFootIk("mixamorig:RightFoot")

		# Ik for the hand:
		arm : cave.Armature = self.animator.armature.get()
		hand = arm.getBone("mixamorig:RightHand")
		pos = self.transf.untransformVector(self.handIkTransf.getPosition())
		#hand.inverseKinematics(pos, 2)
		hand.twoPartIK(pos)
		
	def update(self):
		events = cave.getEvents()
		
	def end(self, scene: cave.Scene):
		pass
	