

class LevelBlueprint:
    def __init__(self):
        self.name_s = None
        self.initPos_t = None

        self.objectBlueprints_l = []
        self.pointLights_l = []

        self.boundingBox = None
        self.colGroups_l = []


class ObjectDefineBlueprint:
    def __init__(self):
        self.name_s = None

        self.static_b = None
        self.initPos_t = None

        self.boundingBox = None

        self.rendererBlueprints_l = []
        self.colliders_l = []
        self.colGroupTargets_l = []


class ObjectUseBlueprint:
    def __init__(self):
        self.name_s = None
        self.templateName_s = None

        self.static_b = None
        self.initPos_t = None

        self.colGroupTargets_l = []


class ObjectObjStaticBlueprint:
    def __init__(self):

        # Stored in ObjectInitInfo
        self.name_s = None
        self.objFileName_s = None

        self.static_b = None
        self.initPos_t = None

        self.colliders_l = []
        self.colGroupTargets_l = []


class RendererBlueprint:
    def __init__(self):
        self.name_s = None
        self.initPos_t = None
        self.static_b = None

        self.vertexNdarray = None
        self.texCoordNdarray = None
        self.normalNdarray = None

        self.textureDir_s = None

        self.textureVerNum_f = None
        self.textureHorNum_f = None

        self.specularStrength_f = None
        self.shininess_f = None

        self.maxpos_temp = None
        self.minpos_temp = None

        self.pos00_temp = None
        self.pos01_temp = None
        self.pos10_temp = None
        self.pos11_temp = None


class ColliderAabbBlueprint:
    def __init__(self):
        self.name_s = None
        self.initPos_t = None
        self.static_b = None

        self.max_t = None
        self.min_t = None

        self.weight_f = None

        self.bounding = False
        self.blocking = False
        self.trigger = False

        self.activateOption_i = None  # 1 : once, 2 : toggle

        self.triggerCommand_l = []


class PointLightBlueprint:
    def __init__(self):
        self.name_s = None
        self.initPos_t = None
        self.static_b = None

        self.color_t = None
        self.maxDistance_f = None
