from typing import List

import collide as co
from resource_manager import ResourceManager
from player import Player


class LogicalDude:
    def __init__(self, resourceMan:ResourceManager, player:Player, commandQueue_l:List[str], globalState):
        self.resourceMan = resourceMan
        self.player = player
        self.commandQueue_l = commandQueue_l
        self.globalState = globalState

    def update(self) -> None:
        self.player.applyPhysics(self.globalState.freezeLogic_b)

        self.__applyCollision()

    def __applyCollision(self) -> None:
        aabbColCheckCount_i = 0
        aabbDistCheckCount_i = 0

        self.player.nearbyTriggers = []

        for level in self.resourceMan.levelsGen():
            aabbColCheckCount_i += 1
            if not co.checkCollision(self.player.biggerBoundingBoxAabb, self.player, level.boundingBox, level):
                continue

            colGroupQuerys_set = set()
            for aabb in level.colGroups_l:
                aabbColCheckCount_i += 1
                if co.checkCollision(self.player.biggerBoundingBoxAabb, self.player, aabb, level):
                    colGroupQuerys_set.add(aabb.getName())

            # print(colGroupQuerys_set)

            for obj in level.objects_l:
                # Skip if col group is not activated
                skip_b = False
                for colGroupName_s in obj.colGroupTargets_l:
                    if colGroupName_s not in colGroupQuerys_set:
                        skip_b = True
                        break
                if skip_b:
                    continue

                # check bounding box
                boundingChecksOut_b = False
                aabbColCheckCount_i += 1
                if obj.boundingBox is None:
                    boundingChecksOut_b = True
                else:
                    aabbColCheckCount_i += 1
                    if co.checkCollision(self.player.biggerBoundingBoxAabb, self.player, obj.boundingBox, obj):
                        boundingChecksOut_b = True

                if boundingChecksOut_b:
                    for collider in obj.colliders_l:
                        bounding_b, blocking_b, trigger_b = collider.getTypes()
                        if trigger_b and collider.activateOption_i == 3:  # key press
                            self.player.nearbyTriggers += collider.getTriggerCommands()[:]

                        aabbColCheckCount_i += 1
                        if co.checkCollision(self.player.boundingBoxAabb, self.player, collider, obj):
                            if blocking_b:
                                aabbDistCheckCount_i += 1
                                a = co.getDistaceToPushBack(self.player.boundingBoxAabb, self.player, collider, obj)
                                self.player.setPosX(self.player.getPosX() + a[0])
                                self.player.setPosY(self.player.getPosY() + a[1])
                                self.player.setPosZ(self.player.getPosZ() + a[2])

                                if not obj.getStatic():
                                    obj.setPosX(obj.getPosX() + a[3])
                                    obj.setPosY(obj.getPosY() + a[4])
                                    obj.setPosZ(obj.getPosZ() + a[5])

                            if trigger_b:
                                if collider.activateOption_i == 2:  # toggle
                                    self.commandQueue_l += collider.getTriggerCommands()[:]
                                elif collider.activateOption_i == 1:
                                    if not collider.lastState_b:  # once
                                        self.commandQueue_l += collider.getTriggerCommands()[:]
                                        collider.lastState_b = True
                        else:
                            collider.lastState_b = False

        #print("Collision check count:", aabbColCheckCount_i)
        #print("Collision dist count:", aabbDistCheckCount_i)
