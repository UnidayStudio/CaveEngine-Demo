#editoronly

import cave

# This is meant for you to create your own Editor Tab Tools.
# In order to run it, in the Text Editor, go to:
# > Editor Tools... > Register Debug Tab... > ExampleTab
class ExampleTab(cave.ui.DebugTab):
	def __init__(self):
		super().__init__()
		self.counter = 0

	def draw(self):
		ui.text("This is a Sample Tool!")
		ui.separator()
		ui.text("You can modify the Counter below of click the Button to increase it.")
		self.counter = ui.prop("Counter", self.counter)
		if ui.button("Increase counter +1"):
			self.counter += 1
			print("Counter Increased by +1!")
	
