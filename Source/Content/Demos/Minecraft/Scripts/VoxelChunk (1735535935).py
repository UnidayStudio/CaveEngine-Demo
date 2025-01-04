import cave

class VoxelChunk(cave.Component):
	"""
	This Component will be responsible to build the Mesh and Physics for a given
	chunk for the Map. It will also store, in the self.voxels variable, the current
	state of each voxel.
	"""

	def start(self, scene: cave.Scene):
		self.transf = self.entity.getTransform()

		self.meshCmp : cave.MeshComponent = self.entity.add("MeshComponent")
		self.meshCmp.material.setAsset("TestMAT Regular")
		self.meshCmp.mesh.makeLocalNew()
		self.meshCmp.reload()

		self.rbCmp : cave.RigidBodyComponent = self.entity.add("RigidBodyComponent")

		self.gridSize = self.entity.properties.get("gridSize", 32)

		# The mesh:
		self.mesh : cave.Mesh = self.meshCmp.mesh.get()
		
		# The 3D array for each voxel, 0 means empty
		self.voxels = [[[0 for _ in range(self.gridSize)] for _ in range(self.gridSize)] for _ in range(self.gridSize)]
		
		pos = self.transf.worldPosition
		self.generateChunkVoxels(pos.x / self.gridSize, pos.z / self.gridSize)
		self.buildVoxelMesh()
		
	def generateChunkVoxels(self, posX = 0, posY = 0):
		"""
		This method will use perlin noise to procedurally generate this chunk's voxels.
		"""
		perlinScale = 1.1

		# Negative values will not work...
		posX = abs(posX + 100.0)
		posY = abs(posY + 100.0)

		heights = []

		for x in range(self.gridSize):
			for z in range(self.gridSize):
				height = cave.random.perlin(
					(x / self.gridSize + posX) * perlinScale, 
					(z / self.gridSize + posY) * perlinScale
				) * 0.5 + 0.5
				heights.append(height)
				height *= self.gridSize

				for y in range(self.gridSize):
					self.voxels[z][y][x] = 1 if y <= height else 0 
		
	def buildVoxelMesh(self):
		"""
		Given the self.voxels, it will build a custom mesh for them, submitting it to the GPU
		and also using it as the Physics Mesh for the collisions.
		"""
		self.mesh.reset()
		
		self.vertices = []
		self.indices = []

		def addFace(offset, normal, tangent, uvOffsets):
			vertexBase = len(self.vertices)
			self.vertices.extend([
				cave.Vertex(offset[0], normal, tangent, uvOffsets[0]),
				cave.Vertex(offset[1], normal, tangent, uvOffsets[1]),
				cave.Vertex(offset[2], normal, tangent, uvOffsets[2]),
				cave.Vertex(offset[3], normal, tangent, uvOffsets[3])
			])
			self.indices.extend([
				vertexBase, vertexBase + 2, vertexBase + 1,
				vertexBase + 3, vertexBase + 2, vertexBase
			])

		# Cube face definitions
		faces = [
			{"dir": (0, 0,  1), "offsets": [(0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 1)]}, # Front
			{"dir": (0, 0, -1), "offsets": [(1, 1, 0), (0, 1, 0), (0, 0, 0), (1, 0, 0)]}, # Back
			{"dir": (0,  1, 0), "offsets": [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)]}, # Top
			{"dir": (0, -1, 0), "offsets": [(0, 0, 1), (1, 0, 1), (1, 0, 0), (0, 0, 0)]}, # Bottom
			{"dir": ( 1, 0, 0), "offsets": [(1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0)]}, # Right
			{"dir": (-1, 0, 0), "offsets": [(0, 0, 1), (0, 0, 0), (0, 1, 0), (0, 1, 1)]}  # Left
		]

		# Generate mesh
		for x in range(self.gridSize):
			for y in range(self.gridSize):
				for z in range(self.gridSize):
					if self.voxels[z][y][x] == 0:
						continue

					for face in faces:
						nx, ny, nz = x + face["dir"][0], y + face["dir"][1], z + face["dir"][2]
						if nx < 0 or ny < 0 or nz < 0 or nx >= self.gridSize or ny >= self.gridSize or nz >= self.gridSize or self.voxels[nz][ny][nx] == 0:
							offsets = [(cave.Vector3(v[0] + x, v[1] + y, v[2] + z)) for v in face["offsets"]]
							uvOffsets = [cave.Vector2(0, 0), cave.Vector2(1, 0), cave.Vector2(1, 1), cave.Vector2(0, 1)]
							addFace(offsets, cave.Vector3(*face["dir"]), cave.Vector3(1, 0, 0), uvOffsets)

		for vertex in self.vertices:
			self.mesh.appendVertex(vertex.position, vertex.normal, vertex.tangent, vertex.uv)

		self.mesh.indices = self.indices

		self.mesh.recalculateTangents()
		
		# Send Mesh to GPU:
		self.mesh.reload() 

		# Updating the Physics:
		self.rbCmp.mesh.makeWeakRef(self.mesh)
		self.rbCmp.reload()

	def normalizePos(self, pos : cave.Vector3, local=False) -> cave.Vector3:
		"""
		This methid will convert a regular, world position vector into a local 
		one that can be used to access the self.voxels matrix.
		"""
		if not local:
			pos = self.transf.untransformVector(pos)
		pos.x = cave.math.floor(pos.x) + 0.5
		pos.y = cave.math.floor(pos.y) + 0.5
		pos.z = cave.math.floor(pos.z) + 0.5		
		return pos
	
	def isValidPos(self, pos : cave.Vector3) -> bool:
		"""
		Checks to see if the positin is within the Chunk range.
		"""
		
		if pos.x < 0 or pos.y < 0 or pos.z < 0:
			return False
		elif pos.x >= self.gridSize or pos.y >= self.gridSize or pos.z >= self.gridSize:
			return False
		return True
	
	def setBlock(self, value: int, pos : cave.Vector3, local=False) -> bool:
		pos = self.normalizePos(pos, local)
		if not self.isValidPos(pos):
			return False
		
		self.voxels[int(pos.z)][int(pos.y)][int(pos.x)] = value

		self.buildVoxelMesh()
		return True	
	
	def getBlock(self, pos : cave.Vector3, local=False) -> int:
		pos = self.normalizePos(pos, local)
		if not self.isValidPos(pos):
			return -1
		return self.voxels[int(pos.z)][int(pos.y)][int(pos.x)]

	def addBlock(self, pos : cave.Vector3, local=False) -> bool:
		return self.setBlock(1, pos, local)
	
	def removeBlock(self, pos : cave.Vector3, local=False) -> bool:
		return self.setBlock(0, pos, local)

	def update(self):
		events = cave.getEvents()
		
	def end(self, scene: cave.Scene):
		pass
	