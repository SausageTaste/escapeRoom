import json

import const


class Configs:
    def __init__(self):
        # init
        self.fullScreen_b = None
        self.initScreenSizeWidth_i = None
        self.initScreenSizeHeight_i = None

        # graphic
        self.drawFlashLightShadow_b = None

        # control
        self.mouseSensitivity_f = None
        self.keyboardLookSensitivity_f = None

        self.loadJson()

    def loadJson(self):
        with open(const.CONFIGS_FILE_s, encoding="utf8") as file:
            a = json.load(file)

        self.fullScreen_b = a["fullScreen_b"]
        self.initScreenSizeWidth_i = a["initScreenSizeWidth_i"]
        self.initScreenSizeHeight_i = a["initScreenSizeHeight_i"]

        self.drawFlashLightShadow_b = a["drawFlashLightShadow_b"]
        self.mouseSensitivity_f = a["mouseLookSensitivity_f"]
        self.keyboardLookSensitivity_f = a["keyboardLookSensitivity_f"]

def main():
    a = Configs()
    print(a.mouseSensitivity_f)

if __name__ == '__main__':
    main()
