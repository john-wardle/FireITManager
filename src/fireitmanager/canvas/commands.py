"""Placeholder for future command implementations."""

class Command:
    """Base class for all commands."""
    
    def execute(self):
        pass
    
    def undo(self):
        pass

# Example command
class AddBuildingCommand(Command):
    """Command to add a building to the scene."""
    
    def __init__(self, scene, model):
        self.scene = scene
        self.model = model
        
    def execute(self):
        self.building_item = self.scene.addBuilding(model=self.model)
        
    def undo(self):
        self.scene.removeItem(self.building_item)