import collide as co
from physics import PhysicsActor
from light import SpotLight
import mmath as mm

class Player(PhysicsActor):
    moveSpeed_f = 5.0

    def __init__(self):
        super().__init__("player", (0.0, 1.0, 0.0) )

        self.nearbyTriggers = []

        self.boundingBoxAabb = co.Aabb(
            (-0.4, 0.0,-0.4 ), (0.4, 1.8, 0.4), "player_boudingbox", 10, (0.0, 0.0, 0.0), False, True, True, False, [], 2
        )

        self.flashLightOn_b = True
        self.flashLight = SpotLight( "flashlight", False, (0.0, 1.4, 0.0), (0.8, 0.8, 0.8), 30.0, 30.0)
        self.flashLight.genShadowMap()

        self.segment = co.Segment("aim", False, (0.0, 1.6, 0.0), mm.Vec4(0, 0, -1000, 0))

        self.biggerBoundingBoxAabb = co.Aabb(
            (-2, -1,-2 ), (2, 3, 2), "player_reach_area", 10, (0.0, 0.0, 0.0), False, True, True, False, [], 2
        )