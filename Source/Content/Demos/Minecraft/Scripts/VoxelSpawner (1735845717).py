import cave
import cave.math

class VoxelSpawner(cave.Component):
	"""
	This component is meant to be in the Player and it will control the
	Chunk spawn that is necessary in order to procedurally continue to
	build the world as you move around.
	"""

	gridSize   = 16
	
	spawnRange = 1
	initialSpawnRange = 3

	def start(self, scene: cave.Scene):
		self.transf = self.entity.getTransform()

		self.chunks = scene.newEntity()
		self.chunks.name = "Chunk Parts"

		self.chunkBase = scene.get("ChunkBase")

		self.spawnChunks(self.initialSpawnRange)

	def getChunk(self, worldPos) -> cave.Entity:
		pos = worldPos / self.gridSize
		pos.x = cave.math.floor(pos.x)
		pos.z = cave.math.floor(pos.z)
		chunkName = f"{int(pos.x)}x{int(pos.z)}"
		return self.chunks.getChild(chunkName, False)

	def spawnChunks(self, spawnRange=1):
		scene = self.entity.getScene()

		pos = self.transf.worldPosition / self.gridSize
		pos.x = cave.math.floor(pos.x)
		pos.z = cave.math.floor(pos.z)

		for x in range(-spawnRange, spawnRange + 1):
			for z in range(-spawnRange, spawnRange + 1):
				chunkName = f"{int(pos.x + x)}x{int(pos.z + z)}"
				child = self.chunks.getChild(chunkName, False)

				if not child:
					# Needs to add a new Chunk!
					child = scene.copyEntity(self.chunkBase)
					child.name = chunkName
					child.getTransform().setPosition((pos.x + x) * self.gridSize, 0, (pos.z + z) * self.gridSize)
					child.setParent(self.chunks)
					child.properties["gridSize"] = self.gridSize
					child.activate(scene)

					# As an optimization, we can return from the funcion here to make sure 
					# that only one chunk gets spawned per frame, avoding huge frame drops.
					return

	def update(self):
		self.spawnChunks(self.spawnRange)
		
	def end(self, scene: cave.Scene):
		pass
	