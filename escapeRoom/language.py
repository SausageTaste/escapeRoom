


class UiTexts:
    def __init__(self):
        self.__title_s = "Escape Room"
        self.__resumeGame_s = "계속"
        self.__startNewGame_s = "처음부터 시작"
        self.__loadGame_s = "불러오기"
        self.__settings_s = "설정"
        self.__exit_s = "나가기"

    def getMenuTexts(self):
        return (
            self.__title_s, self.__resumeGame_s, self.__startNewGame_s, self.__loadGame_s, self.__settings_s,
            self.__exit_s
        )