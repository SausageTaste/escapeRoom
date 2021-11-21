import time
import os
from typing import Optional, List
from multiprocessing import Process, Queue
from threading import Thread
from queue import Empty

import numpy as np

import mmath as mm

import data_struct as ds
import blueprints as bp
import collide as co
import light as li


class CompileErrorSmll(Exception):
    def __init__(self, lineNo_i:int, type_s:str, name_s:Optional[str], errorCode_i:int, *args):
        """
        error codes
        1 : Systax error (wrongCode:str)
        2 : Invalid keyword (wrongCode:str)
        3 : Invalid arguments for function (function:str, arguments:iter)
        4 : Not existing function (function:str)
        5 : A value is not defined (valueName:str)
        6 : Compiler flaw (text:str)
        7 : Already taken name (name:str)
        """
        self.lineNo_i = int(lineNo_i)
        self.type_s = str(type_s)
        if name_s is None:
            self.name_s  = "unknown"
        else:
            self.name_s = str(name_s)
        self.errorCode_i = int(errorCode_i)
        self.args_t = args

    def __str__(self):
        commonText_s = "[line {} in {} '{}'] ".format(self.lineNo_i, self.type_s, self.name_s)
        if self.errorCode_i == 0:
            return "[line {}] {}".format(self.lineNo_i, self.args_t[0])
        elif self.errorCode_i == 1:
            return commonText_s + "Syntax error: \"{}\"".format(self.args_t[0])
        elif self.errorCode_i == 2:
            return commonText_s + "Invalid keyword: \"{}\"".format(self.args_t[0])
        elif self.errorCode_i == 3:
            return commonText_s + "Invalid arguments for function '{}': {}".format(self.args_t[0], tuple(self.args_t[1]))
        elif self.errorCode_i == 4:
            return commonText_s + "This function does not exist: '{}'".format(self.args_t[0])
        elif self.errorCode_i == 5:
            return commonText_s + "'{}' is not defined".format(self.args_t[0])
        elif self.errorCode_i == 6:
            return commonText_s + "This is bug. Please report this whole error message to developer: \"{}\"".format(self.args_t[0])
        elif self.errorCode_i == 7:
            return "[in level '{}'] The name '{}' is already taken.".format(self.name_s, self.args_t[0])
        else:
            raise "Error code '{}' is not valid.".format(self.errorCode_i)


class LevelLoader(Process):
    def __init__(self, toMainQueue:Queue, toProcQueue:Queue):
        super().__init__()

        self.toMainQueue = toMainQueue
        self.toProcQueue = toProcQueue

        self.run_b = True

    def run(self) -> None:
        while self.run_b:
            try:
                smllFileDir_s = self.toProcQueue.get_nowait()
            except Empty:
                pass
            else:
                if not os.path.isfile(smllFileDir_s):
                    self.toMainQueue.put( (-1, smllFileDir_s) )
                    continue

                smllCompiler = SmllCompiler(smllFileDir_s)
                st = time.time()
                level = smllCompiler.compile()
                print("Compilation complete: '{}' ({:.4f} sec)".format(level.getName(), time.time() - st) )

                self.toMainQueue.put(level)

    def terminate(self):
        self.run_b = False
        try:
            super().terminate()
        except AttributeError:
            pass

        print("Thread 'LevelLoader' terminated")


class SmllCompiler:
    def __init__(self, fileDir_s:str, print_b:bool=False):
        self.__fileDir_s = fileDir_s

        self.__print_b = bool(print_b)

    def compile(self) -> ds.Level:
        headCut_i = self.__fileDir_s.rindex('\\') + 1
        tailCut_i = self.__fileDir_s.index('.', headCut_i)
        fileName_s = self.__fileDir_s[headCut_i:tailCut_i]
        with open(self.__fileDir_s) as file:
            fileData_l = file.readlines()

        fileData_l = self.makeTextClear(fileData_l)

        levelBprint = bp.LevelBlueprint()
        levelBprint.name_s = fileName_s
        level = self.takeLevelBlock(fileData_l, levelBprint)
        self.checkNameDuplicate(level)

        if self.__print_b:
            print(level.getName())
            for x in level.objectBlueprints_l:
                print(x)
                for y in x.__dir__():
                    if not y.startswith("__"):
                        print("\t{} : {}".format(y, x.__getattribute__(y)))
                print()
                for z in x.rendererBlueprints_l:
                    print("\t{}".format(z))
                    for w in z.__dir__():
                        if not w.startswith("__"):
                            print("\t\t{} : {}".format(w, z.__getattribute__(w)))
                print()
                for z in x.colliders_l:
                    print("\t{}".format(z))
                    for w in z.__dir__():
                        if not w.startswith("__"):
                            print("\t\t{} : {}".format(w, z.__getattribute__(w)))
                print()

        return level

    @staticmethod
    def deleteWhiteSpaces(a:str) -> str:
        newString_l = []
        inString_b = False
        for x_s in a:
            if inString_b:
                if x_s == '"':
                    inString_b = False
                else:
                    newString_l.append(x_s)
            else:
                if x_s == '"':
                    inString_b = True
                else:
                    for y_s in (' ', '\t', '\n'):
                        if x_s == y_s:
                            break
                    else:
                        newString_l.append(x_s)
        return ''.join(newString_l)
    @classmethod
    def makeTextClear(cls, fileData_l: list) -> List[str]:
        commentBlock_b = False
        commentBlockOpenedLineNo_i = -1

        for x, x_s in enumerate(fileData_l):
            x_s = cls.deleteWhiteSpaces(x_s)
            x_s = x_s.lower()

            #### Remove /* */ comment blocks ####

            if x_s.count("/*"):
                commentIndex_i = x_s.index("/*")
                x_s = x_s[:commentIndex_i]
                commentBlock_b = True
                commentBlockOpenedLineNo_i = x + 1
            if x_s.count("*/"):
                if commentBlock_b:
                    commentIndex_i = x_s.index("*/") + 2
                    x_s = x_s[commentIndex_i:]
                    commentBlock_b = False
                else:
                    raise CompileErrorSmll(x + 1, "level", None, 0, "Comment block closes without ever opened")
            if commentBlock_b and not x_s.count("/*") and not x_s.count("*/"):
                x_s = ""

            #### Remove // commenet ####
            if x_s.count("//"):
                commentIndex_i = x_s.index("//")
                x_s = x_s[:commentIndex_i]

            fileData_l[x] = x_s

        if commentBlock_b:
            raise CompileErrorSmll(commentBlockOpenedLineNo_i, "level", None, 0, "Comment block does not close")

        ####  ####

        return fileData_l

    ######## Level ########

    @classmethod
    def takeLevelBlock(cls, fileData_l:list, levelBprint:bp.LevelBlueprint) -> ds.Level:
        accumKeyword_l = []
        accumBlock_l = []
        workingToken_i = 0
        curBlockDepth_i = 0
        blockStartLineIndex_i = -1

        for x, x_s in enumerate(fileData_l):
            accumLine_l = []
            lineIndex_i = x

            foundInThisLoop_b = False

            if workingToken_i > 0 and blockStartLineIndex_i == -1:
                blockStartLineIndex_i = lineIndex_i

            for y_s in x_s:
                if workingToken_i == 0:
                    if y_s == "{":
                        keyword_s = ''.join(accumKeyword_l)
                        accumKeyword_l = []
                        if keyword_s == "object::define":
                            workingToken_i = 1
                            curBlockDepth_i = 1
                            foundInThisLoop_b = True
                        elif keyword_s == "object::objstatic":
                            workingToken_i = 6
                            curBlockDepth_i = 1
                            foundInThisLoop_b = True
                        elif keyword_s == "object::use":
                            workingToken_i = 3
                            curBlockDepth_i = 1
                            foundInThisLoop_b = True
                        elif keyword_s == "light::pointlight":
                            workingToken_i = 2
                            curBlockDepth_i = 1
                            foundInThisLoop_b = True
                        elif keyword_s == "bounding::aabb":
                            workingToken_i = 4
                            curBlockDepth_i = 1
                            foundInThisLoop_b = True
                        elif keyword_s == "colgroup::aabb":
                            workingToken_i = 5
                            curBlockDepth_i = 1
                            foundInThisLoop_b = True
                        else:
                            raise CompileErrorSmll(lineIndex_i + 1, "level", levelBprint.name_s, 2, keyword_s)

                    elif y_s == ";":  # Found a function
                        funcName_s, args_s = "".join(accumKeyword_l).split('(')
                        accumKeyword_l = []
                        cls.applyLevelFunction(levelBprint, funcName_s, args_s, lineIndex_i)
                    else:
                        accumKeyword_l.append(y_s)
                elif workingToken_i > 0:
                    if blockStartLineIndex_i == -1:
                        blockStartLineIndex_i = lineIndex_i

                    if y_s == "{":
                        curBlockDepth_i += 1
                        accumLine_l.append(y_s)
                    elif y_s == "}":
                        curBlockDepth_i -= 1
                        if curBlockDepth_i == 0:
                            if workingToken_i == 1:
                                levelBprint.objectBlueprints_l.append( cls.takeObjectDefineBlock(accumBlock_l, blockStartLineIndex_i) )
                                accumBlock_l = []
                                workingToken_i = 0
                                blockStartLineIndex_i = -1
                            elif workingToken_i == 2:
                                levelBprint.pointLights_l.append( cls.takePointLightBlock(accumBlock_l, blockStartLineIndex_i) )
                                accumBlock_l = []
                                workingToken_i = 0
                                blockStartLineIndex_i = -1
                            elif workingToken_i == 3:
                                levelBprint.objectBlueprints_l.append( cls.takeObjectUseBlock(accumBlock_l, blockStartLineIndex_i) )
                                accumBlock_l = []
                                workingToken_i = 0
                                blockStartLineIndex_i = -1
                            elif workingToken_i == 4:
                                if levelBprint.boundingBox is None:
                                    levelBprint.boundingBox = cls.takeBoundingAabbBlock(accumBlock_l, blockStartLineIndex_i)
                                    accumBlock_l = []
                                    workingToken_i = 0
                                    blockStartLineIndex_i = -1
                                else:
                                    raise FileExistsError
                            elif workingToken_i == 6:  # object::objstatic
                                levelBprint.objectBlueprints_l.append( cls.takeObjectObjStaticBlock(accumBlock_l, blockStartLineIndex_i) )
                                accumBlock_l = []
                                workingToken_i = 0
                                blockStartLineIndex_i = -1
                            elif workingToken_i == 5:
                                levelBprint.colGroups_l.append( cls.takeBoundingAabbBlock(accumBlock_l, blockStartLineIndex_i) )
                                accumBlock_l = []
                                workingToken_i = 0
                                blockStartLineIndex_i = -1
                            else:
                                raise ValueError
                        else:
                            accumLine_l.append(y_s)
                    else:
                        accumLine_l.append(y_s)

            if workingToken_i > 0:
                if accumLine_l:
                    accumBlock_l.append(accumLine_l)
                else:
                    if not foundInThisLoop_b:
                        accumBlock_l.append([])

        cls.checkLevel(levelBprint, 0)
        return cls.makeLevel(levelBprint)
    @staticmethod
    def applyLevelFunction(levelBprint:bp.LevelBlueprint, funcName_s:str, args_s:str, lineIndex_i:int) -> None:
        args_s = args_s[:-1]
        args_l = args_s.split(',')
        del args_s

        lineNo_i = lineIndex_i + 1

        if funcName_s == "initpos":
            if not len(args_l) == 3:
                raise CompileErrorSmll(lineNo_i, "level", levelBprint.name_s, 3, "initpos(float, float, float)", args_l)
            try:
                levelBprint.initPos_t = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "level", levelBprint.name_s, 3, "initpos(float, float, float)", args_l)
        else:
            raise CompileErrorSmll(lineNo_i, "level", levelBprint.name_s, 4, funcName_s)
    @staticmethod
    def checkLevel(levelBprint:bp.LevelBlueprint, startLineIndex_i:int) -> None:
        if levelBprint.name_s is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "level", levelBprint.name_s, 5, "name")
        elif levelBprint.initPos_t is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "level", levelBprint.name_s, 5, "initpos")
        elif levelBprint.boundingBox is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "level", levelBprint.name_s, 5, "bounding::aabb")
    @staticmethod
    def makeLevel(levelBprint:bp.LevelBlueprint) -> ds.Level:
        level = ds.Level(levelBprint.name_s, levelBprint.initPos_t)
        level.objectBlueprints_l = levelBprint.objectBlueprints_l
        level.pointLights_l = levelBprint.pointLights_l
        level.boundingBox = levelBprint.boundingBox
        level.colGroups_l = levelBprint.colGroups_l
        return level

    ######## Objects ########

    @classmethod
    def takeObjectDefineBlock(cls, objectData_l:list, startLineIndex_i:int) -> bp.ObjectDefineBlueprint:
        tokenFunctions_d = {
            "renderer::aab": cls.takeRendererAabBlock,
            "renderer::quad": cls.takeRendererQuadBlock,
            
            'collider::aabb': cls.takeColliderAabbBlock,
        }

        objBprint = bp.ObjectDefineBlueprint()

        accumKeyword_l = []
        accumBlock_l = []
        workingToken_i = 0
        curBlockDepth_i = 0
        workingTokenFunc = None
        blockStartLineIndex_i = -1

        for x, x_l in enumerate(objectData_l):
            accumLine_l = []
            lineIndex_i = x + startLineIndex_i

            foundInThisLoop_b = False

            if workingToken_i > 0 and blockStartLineIndex_i == -1:
                blockStartLineIndex_i = lineIndex_i

            for y_s in x_l:
                if workingToken_i == 0:  # While block is not found
                    if y_s == "{":  # Found a block
                        keywordAndType_s = ''.join(accumKeyword_l)
                        keyword_s, _ = keywordAndType_s.split("::")

                        accumKeyword_l = []
                        if keyword_s == "renderer":
                            workingToken_i = 1  # renderer
                            workingTokenFunc = tokenFunctions_d[keywordAndType_s]
                            curBlockDepth_i = 1
                            foundInThisLoop_b = True
                        elif keyword_s == "collider":
                            workingToken_i = 2  # collider
                            workingTokenFunc = tokenFunctions_d[keywordAndType_s]
                            curBlockDepth_i = 1
                            foundInThisLoop_b = True
                        else:
                            raise CompileErrorSmll( lineIndex_i + 1, "object", objBprint.name_s, 2, keywordAndType_s )
                    elif y_s == ";":  # Found a function
                        funcName_s, args_s = "".join(accumKeyword_l).split('(')
                        accumKeyword_l = []
                        cls.applyObjectDefineFunction(objBprint, funcName_s, args_s, lineIndex_i)
                    else:
                        accumKeyword_l.append(y_s)
                elif workingToken_i > 0:  # Process block
                    if blockStartLineIndex_i == -1:
                        blockStartLineIndex_i = lineIndex_i

                    if y_s == "{":
                        curBlockDepth_i += 1
                        accumLine_l.append(y_s)
                    elif y_s == "}":
                        curBlockDepth_i -= 1
                        if curBlockDepth_i == 0:
                            if workingToken_i == 1:
                                objBprint.rendererBlueprints_l.append( workingTokenFunc(accumBlock_l, blockStartLineIndex_i) )
                            elif workingToken_i == 2:
                                aCollider = workingTokenFunc(accumBlock_l, blockStartLineIndex_i)
                                objBprint.colliders_l.append( aCollider )
                                if aCollider.getTypes()[0]:
                                    if objBprint.boundingBox is None:
                                        objBprint.boundingBox = aCollider
                                    else:
                                        raise CompileErrorSmll(0, "object", objBprint.name_s, 0, "tow bounding box")

                            accumBlock_l = []
                            workingToken_i = 0
                            blockStartLineIndex_i = -1
                        else:
                            accumLine_l.append(y_s)
                    else:
                        accumLine_l.append(y_s)

            if workingToken_i > 0:
                if accumLine_l:
                    accumBlock_l.append(accumLine_l)
                else:
                    if not foundInThisLoop_b:
                        accumBlock_l.append([])

        cls.checkObjectDefine(objBprint, startLineIndex_i)

        return objBprint
    @staticmethod
    def applyObjectDefineFunction(objBprint:bp.ObjectDefineBlueprint, funcName_s:str, args_s:str, lineIndex_i:int) -> None:
        args_s = args_s[:-1]
        args_l = args_s.split(',')
        del args_s

        lineNo_i = lineIndex_i + 1

        if funcName_s == "static":
            if args_l[0] == "true":
                objBprint.static_b = True
            elif args_l[0] == "false":
                objBprint.static_b = False
            else:
                raise CompileErrorSmll( lineNo_i, "object", objBprint.name_s, 3, "static(bool)", args_l )
        elif funcName_s == "initpos":
            if not len(args_l) == 3:
                raise CompileErrorSmll( lineNo_i, "object", objBprint.name_s, 3, "initpos(float, float, float)", args_l )
            try:
                objBprint.initPos_t = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll( lineNo_i, "object", objBprint.name_s, 3, "initpos(float, float, float)", args_l )
        elif funcName_s == "name":
            if len(args_l) != 1:
                raise CompileErrorSmll( lineNo_i, "object", objBprint.name_s, 3, "name(str)", args_l )
            objBprint.name_s = args_l[0]
        elif funcName_s == "colgrouptargets":
            objBprint.colGroupTargets_l += args_l
        else:
            raise CompileErrorSmll( lineNo_i, "object", objBprint.name_s, 4, funcName_s )
    @staticmethod
    def checkObjectDefine(obp:bp.ObjectDefineBlueprint, startLineIndex_t:int) -> None:
        if obp.name_s is None:
            raise CompileErrorSmll(startLineIndex_t + 1, "object", None, 5, "name")
        elif obp.static_b is None:
            raise CompileErrorSmll(startLineIndex_t + 1, "object", None, 5, "static")
        elif obp.initPos_t is None:
            raise CompileErrorSmll(startLineIndex_t + 1, "object", None, 5, "initpos")

    @classmethod
    def takeObjectUseBlock(cls, objectData_l: list, startLineIndex_i: int) -> bp.ObjectUseBlueprint:
        objBprint = bp.ObjectUseBlueprint()

        accumKeyword_l = []
        accumBlock_l = []
        workingToken_i = 0
        blockStartLineIndex_i = -1

        for x, x_l in enumerate(objectData_l):
            accumLine_l = []
            lineIndex_i = x + startLineIndex_i

            foundInThisLoop_b = False

            if workingToken_i > 0 and blockStartLineIndex_i == -1:
                blockStartLineIndex_i = lineIndex_i

            for y_s in x_l:
                if workingToken_i == 0:  # While block is not found
                    if y_s == ";":  # Found a function
                        funcName_s, args_s = "".join(accumKeyword_l).split('(')
                        accumKeyword_l = []
                        cls.applyObjectUseFunction(objBprint, funcName_s, args_s, lineIndex_i)
                    else:
                        accumKeyword_l.append(y_s)

            if workingToken_i > 0:
                if accumLine_l:
                    accumBlock_l.append(accumLine_l)
                else:
                    if not foundInThisLoop_b:
                        accumBlock_l.append([])

        cls.checkObjectUse(objBprint, startLineIndex_i)

        return objBprint
    @staticmethod
    def applyObjectUseFunction(objBprint:bp.ObjectUseBlueprint, funcName_s:str, args_s:str, lineIndex_i:int) -> None:
        args_s = args_s[:-1]
        args_l = args_s.split(',')
        del args_s

        lineNo_i = lineIndex_i + 1

        if funcName_s == "static":
            if args_l[0] == "true":
                objBprint.static_b = True
            elif args_l[0] == "false":
                objBprint.static_b = False
            else:
                raise CompileErrorSmll(lineNo_i, "object", objBprint.name_s, 3, "static(bool)", args_l)
        elif funcName_s == "initpos":
            if not len(args_l) == 3:
                raise CompileErrorSmll(lineNo_i, "object", objBprint.name_s, 3, "initpos(float, float, float)", args_l)
            try:
                objBprint.initPos_t = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "object", objBprint.name_s, 3, "initpos(float, float, float)", args_l)
        elif funcName_s == "name":
            if len(args_l) != 1:
                raise CompileErrorSmll(lineNo_i, "object", objBprint.name_s, 3, "name(str)", args_l)
            objBprint.name_s = args_l[0]
        elif funcName_s == "tempname":
            if len(args_l) != 1:
                raise CompileErrorSmll(lineNo_i, "object", objBprint.name_s, 3, "tempname(str)", args_l)
            objBprint.templateName_s = args_l[0]
        elif funcName_s == "colgrouptargets":
            objBprint.colGroupTargets_l += args_l
        else:
            raise CompileErrorSmll(lineNo_i, "object", objBprint.name_s, 4, funcName_s)
    @staticmethod
    def checkObjectUse(objBprint:bp.ObjectUseBlueprint, startLineIndex_t:int) -> None:
        if objBprint.name_s is None:
            raise CompileErrorSmll(startLineIndex_t + 1, "object", None, 5, "name")
        elif objBprint.static_b is None:
            raise CompileErrorSmll(startLineIndex_t + 1, "object", None, 5, "static")
        elif objBprint.initPos_t is None:
            raise CompileErrorSmll(startLineIndex_t + 1, "object", None, 5, "initpos")
        elif objBprint.templateName_s is None:
            raise CompileErrorSmll(startLineIndex_t + 1, "object", None, 5, "tempname")

    @classmethod
    def takeObjectObjStaticBlock(cls, objectData_l: list, startLineIndex_i: int) -> bp.ObjectObjStaticBlueprint:
        tokenFunctions_d = {
            'collider::aabb':cls.takeColliderAabbBlock,
        }

        objBprint = bp.ObjectObjStaticBlueprint()

        accumKeyword_l = []
        accumBlock_l = []
        workingToken_i = 0
        curBlockDepth_i = 0
        workingTokenFunc = None
        blockStartLineIndex_i = -1

        for x, x_l in enumerate(objectData_l):
            accumLine_l = []
            lineIndex_i = x + startLineIndex_i

            foundInThisLoop_b = False

            if workingToken_i > 0 and blockStartLineIndex_i == -1:
                blockStartLineIndex_i = lineIndex_i

            for y_s in x_l:
                if workingToken_i == 0:  # While block is not found
                    if y_s == "{":  # Found a block
                        keywordAndType_s = ''.join(accumKeyword_l)
                        keyword_s, _ = keywordAndType_s.split("::")

                        accumKeyword_l = []
                        if keyword_s == "collider":
                            workingToken_i = 2  # collider
                            workingTokenFunc = tokenFunctions_d[keywordAndType_s]
                            curBlockDepth_i = 1
                            foundInThisLoop_b = True
                        else:
                            raise CompileErrorSmll(lineIndex_i + 1, "object", objBprint.name_s, 2, keywordAndType_s)
                    elif y_s == ";":  # Found a function
                        funcName_s, args_s = "".join(accumKeyword_l).split('(')
                        accumKeyword_l = []
                        cls.applyObjectObjStaticFunction(objBprint, funcName_s, args_s, lineIndex_i)
                    else:
                        accumKeyword_l.append(y_s)
                elif workingToken_i > 0:  # Process block
                    if blockStartLineIndex_i == -1:
                        blockStartLineIndex_i = lineIndex_i

                    if y_s == "{":
                        curBlockDepth_i += 1
                        accumLine_l.append(y_s)
                    elif y_s == "}":
                        curBlockDepth_i -= 1
                        if curBlockDepth_i == 0:
                            if workingToken_i == 2:
                                aCollider = workingTokenFunc(accumBlock_l, blockStartLineIndex_i)
                                objBprint.colliders_l.append(aCollider)
                                if aCollider.getTypes()[0]:
                                    if objBprint.boundingBox is None:
                                        objBprint.boundingBox = aCollider
                                    else:
                                        raise CompileErrorSmll(0, "object", objBprint.name_s, 0, "two bounding box")

                            accumBlock_l = []
                            workingToken_i = 0
                            blockStartLineIndex_i = -1
                        else:
                            accumLine_l.append(y_s)
                    else:
                        accumLine_l.append(y_s)

            if workingToken_i > 0:
                if accumLine_l:
                    accumBlock_l.append(accumLine_l)
                else:
                    if not foundInThisLoop_b:
                        accumBlock_l.append([])

        cls.checkObjectObjStatic(objBprint, startLineIndex_i)

        return objBprint
    @staticmethod
    def applyObjectObjStaticFunction(objBprint: bp.ObjectObjStaticBlueprint, funcName_s: str, args_s: str, lineIndex_i: int) -> None:
        args_s = args_s[:-1]
        args_l = args_s.split(',')
        del args_s

        lineNo_i = lineIndex_i + 1

        if funcName_s == "static":
            if args_l[0] == "true":
                objBprint.static_b = True
            elif args_l[0] == "false":
                objBprint.static_b = False
            else:
                raise CompileErrorSmll(lineNo_i, "object", objBprint.name_s, 3, "static(bool)", args_l)
        elif funcName_s == "initpos":
            if not len(args_l) == 3:
                raise CompileErrorSmll(lineNo_i, "object", objBprint.name_s, 3, "initpos(float, float, float)",
                                       args_l)
            try:
                objBprint.initPos_t = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "object", objBprint.name_s, 3, "initpos(float, float, float)",
                                       args_l)
        elif funcName_s == "name":
            if len(args_l) != 1:
                raise CompileErrorSmll(lineNo_i, "object", objBprint.name_s, 3, "name(str)", args_l)
            objBprint.name_s = args_l[0]
        elif funcName_s == "objname":
            if len(args_l) != 1:
                raise CompileErrorSmll(lineNo_i, "object", objBprint.name_s, 3, "tempname(str)", args_l)
            objBprint.objFileName_s = args_l[0]
        elif funcName_s == "colgrouptargets":
            objBprint.colGroupTargets_l += args_l
        else:
            raise CompileErrorSmll(lineNo_i, "object", objBprint.name_s, 4, funcName_s)
    @staticmethod
    def checkObjectObjStatic(objBprint: bp.ObjectObjStaticBlueprint, startLineIndex_t: int) -> None:
        if objBprint.name_s is None:
            raise CompileErrorSmll(startLineIndex_t + 1, "object", None, 5, "name")
        elif objBprint.static_b is None:
            raise CompileErrorSmll(startLineIndex_t + 1, "object", None, 5, "static")
        elif objBprint.initPos_t is None:
            raise CompileErrorSmll(startLineIndex_t + 1, "object", None, 5, "initpos")
        elif objBprint.objFileName_s is None:
            raise CompileErrorSmll(startLineIndex_t + 1, "object", None, 5, "objname")

    ######## Object level but not object ########

    @classmethod
    def takeBoundingAabbBlock(cls, objectData_l: list, startLineIndex_i: int) -> co.Aabb:
        colBprint = bp.ColliderAabbBlueprint()

        accumKeyword_l = []
        accumBlock_l = []
        workingToken_i = 0
        blockStartLineIndex_i = -1

        for x, x_l in enumerate(objectData_l):
            accumLine_l = []
            lineIndex_i = x + startLineIndex_i

            foundInThisLoop_b = False

            if workingToken_i > 0 and blockStartLineIndex_i == -1:
                blockStartLineIndex_i = lineIndex_i

            for y_s in x_l:
                if y_s == ";":  # Found a function
                    funcName_s, args_s = "".join(accumKeyword_l).split('(')
                    accumKeyword_l = []
                    cls.applyBoundingAabbFunction(colBprint, funcName_s, args_s, lineIndex_i)
                else:
                    accumKeyword_l.append(y_s)

            if workingToken_i > 0:
                if accumLine_l:
                    accumBlock_l.append(accumLine_l)
                else:
                    if not foundInThisLoop_b:
                        accumBlock_l.append([])

        cls.checkBoundingAabb(colBprint, startLineIndex_i)
        pointLight = cls.makeBoundingAabb(colBprint, startLineIndex_i)

        return pointLight
    @staticmethod
    def applyBoundingAabbFunction(colBprint:bp.ColliderAabbBlueprint, funcName_s: str, args_s: str, lineIndex_i: int) -> None:
        if not isinstance(colBprint, bp.ColliderAabbBlueprint):
            raise ValueError(type(colBprint))
        args_s = args_s[:-1]
        args_l = args_s.split(',')
        del args_s

        lineNo_i = lineIndex_i + 1

        if funcName_s == "name":
            if not len(args_l) == 1:
                raise CompileErrorSmll(lineNo_i, "bounding", colBprint.name_s, 3, "name(str)", args_l)
            try:
                colBprint.name_s = str(args_l[0])
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "bounding", colBprint.name_s, 3, "name(str)", args_l)
        elif funcName_s == "initpos":
            if not len(args_l) == 3:
                raise CompileErrorSmll(lineNo_i, "bounding", colBprint.name_s, 3, "initpos(float, float, float)", args_l)
            try:
                colBprint.initPos_t = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "bounding", colBprint.name_s, 3, "initpos(float, float, float)", args_l)
        elif funcName_s == "static":
            if not len(args_l) == 1:
                raise CompileErrorSmll(lineNo_i, "bounding", colBprint.name_s, 3, "static(bool)", args_l)
            elif args_l[0] == "true":
                colBprint.static_b = True
            elif args_l[0] == "false":
                colBprint.static_b = False
            else:
                raise CompileErrorSmll(lineNo_i, "bounding", colBprint.name_s, 3, "static(bool)", args_l)
        elif funcName_s == "weight":
            if not len(args_l) == 1:
                raise CompileErrorSmll(lineNo_i, "bounding", colBprint.name_s, 3, "weight(float)", args_l)
            try:
                colBprint.weight_f = float(args_l[0])
            except:
                raise CompileErrorSmll(lineNo_i, "bounding", colBprint.name_s, 3, "weight(float)", args_l)
        elif funcName_s == "minpos":
            if not len(args_l) == 3:
                raise CompileErrorSmll(lineNo_i, "bounding", colBprint.name_s, 3, "minpos(float, float, float)", args_l)
            try:
                colBprint.min_t = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "bounding", colBprint.name_s, 3, "minpos(float, float, float)", args_l)
        elif funcName_s == "maxpos":
            if not len(args_l) == 3:
                raise CompileErrorSmll(lineNo_i, "bounding", colBprint.name_s, 3, "maxpos(float, float, float)", args_l)
            try:
                colBprint.max_t = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "bounding", colBprint.name_s, 3, "maxpos(float, float, float)", args_l)
        else:
            raise CompileErrorSmll(lineNo_i, "bounding", colBprint.name_s, 4, funcName_s)
    @staticmethod
    def checkBoundingAabb(colBprint:bp.ColliderAabbBlueprint, startLineIndex_i: int) -> None:
        if colBprint.name_s is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "collider", colBprint.name_s, 5, "name")
        elif colBprint.initPos_t is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "collider", colBprint.name_s, 5, "initpos")
        elif colBprint.weight_f is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "collider", colBprint.name_s, 5, "weight")
        elif colBprint.static_b is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "collider", colBprint.name_s, 5, "static")
        elif colBprint.min_t is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "collider", colBprint.name_s, 5, "minpos")
        elif colBprint.max_t is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "collider", colBprint.name_s, 5, "maxpos")

        colBprint.trigger = False
        colBprint.blocking = False
        colBprint.bounding = True
        colBprint.triggerCommand_l = []
        colBprint.activateOption_i = 1
    @staticmethod
    def makeBoundingAabb(colBprint:bp.ColliderAabbBlueprint, startLineIndex_i: int) -> co.Aabb:
        try:
            return co.Aabb(
                colBprint.min_t, colBprint.max_t, colBprint.name_s, colBprint.weight_f, colBprint.initPos_t,
                colBprint.static_b, colBprint.bounding, colBprint.blocking, colBprint.trigger, colBprint.triggerCommand_l,
                colBprint.activateOption_i
            )
        except:
            raise CompileErrorSmll(startLineIndex_i + 1, "bounding", colBprint.name_s, 0, "shit")

    @classmethod
    def takePointLightBlock(cls, objectData_l:list, startLineIndex_i:int) -> li.PointLight:
        pointLightBprint = bp.PointLightBlueprint()

        accumKeyword_l = []
        accumBlock_l = []
        workingToken_i = 0
        blockStartLineIndex_i = -1

        for x, x_l in enumerate(objectData_l):
            accumLine_l = []
            lineIndex_i = x + startLineIndex_i

            foundInThisLoop_b = False

            if workingToken_i > 0 and blockStartLineIndex_i == -1:
                blockStartLineIndex_i = lineIndex_i

            for y_s in x_l:
                if y_s == ";":  # Found a function
                    funcName_s, args_s = "".join(accumKeyword_l).split('(')
                    accumKeyword_l = []
                    cls.applyPointLightFunction(pointLightBprint, funcName_s, args_s, lineIndex_i)
                else:
                    accumKeyword_l.append(y_s)

            if workingToken_i > 0:
                if accumLine_l:
                    accumBlock_l.append(accumLine_l)
                else:
                    if not foundInThisLoop_b:
                        accumBlock_l.append([])

        cls.checkPointLight(pointLightBprint, startLineIndex_i)
        pointLight = cls.makePointLight(pointLightBprint, startLineIndex_i)

        return pointLight
    @staticmethod
    def applyPointLightFunction(pointLightBprint:bp.PointLightBlueprint, funcName_s:str, args_s:str, lineIndex_i:int) -> None:
        if not isinstance(pointLightBprint, bp.PointLightBlueprint):
            raise ValueError(type(pointLightBprint))
        args_s = args_s[:-1]
        args_l = args_s.split(',')
        del args_s

        lineNo_i = lineIndex_i + 1

        if funcName_s == "name":
            if not len(args_l) == 1:
                raise CompileErrorSmll(lineNo_i, "pointlight", pointLightBprint.name_s, 3, "name(str)", args_l)
            try:
                pointLightBprint.name_s = str(args_l[0])
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "pointlight", pointLightBprint.name_s, 3, "name(str)", args_l)
        elif funcName_s == "initpos":
            if not len(args_l) == 3:
                raise CompileErrorSmll( lineNo_i, "pointlight", pointLightBprint.name_s, 3, "initpos(float, float, float)", args_l )
            try:
                pointLightBprint.initPos_t = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll( lineNo_i, "pointlight", pointLightBprint.name_s, 3, "initpos(float, float, float)", args_l )
        elif funcName_s == "static":
            if not len(args_l) == 1:
                raise CompileErrorSmll(lineNo_i, "pointlight", pointLightBprint.name_s, 3, "static(bool)", args_l)
            elif args_l[0] == "true":
                pointLightBprint.static_b = True
            elif args_l[0] == "false":
                pointLightBprint.static_b = False
            else:
                raise CompileErrorSmll(lineNo_i, "pointlight", pointLightBprint.name_s, 3, "static(bool)", args_l)
        elif funcName_s == "color":
            if not len(args_l) == 3:
                raise CompileErrorSmll( lineNo_i, "pointlight", pointLightBprint.name_s, 3, "color(float, float, float)", args_l )
            try:
                pointLightBprint.color_t = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll( lineNo_i, "pointlight", pointLightBprint.name_s, 3, "color(float, float, float)", args_l )
        elif funcName_s == "maxdist":
            if not len(args_l) == 1:
                raise CompileErrorSmll(lineNo_i, "pointlight", pointLightBprint.name_s, 3, "maxdist(float)", args_l)
            try:
                pointLightBprint.maxDistance_f = float(args_l[0])
            except ValueError:
                raise CompileErrorSmll( lineNo_i, "pointlight", pointLightBprint.name_s, 3, "maxdist(float)", args_l )
        else:
            raise CompileErrorSmll(lineNo_i, "pointlight", pointLightBprint.name_s, 4, funcName_s)
    @staticmethod
    def checkPointLight(pointLight:bp.PointLightBlueprint, startLineIndex_i:int) -> None:
        if pointLight.name_s is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "pointlight", pointLight.name_s, 5, "name")
        elif pointLight.initPos_t is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "pointlight", pointLight.name_s, 5, "initpos")
        elif pointLight.static_b is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "pointlight", pointLight.name_s, 5, "static")
        elif pointLight.color_t is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "pointlight", pointLight.name_s, 5, "color")
        elif pointLight.maxDistance_f is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "pointlight", pointLight.name_s, 5, "maxdist")
    @staticmethod
    def makePointLight(pointLightBprint:bp.PointLightBlueprint, startLineIndex_i:int) -> li.PointLight:
        try:
            return li.PointLight(
                pointLightBprint.name_s, pointLightBprint.static_b, pointLightBprint.initPos_t, pointLightBprint.color_t,
                pointLightBprint.maxDistance_f
            )
        except:
            raise CompileErrorSmll(startLineIndex_i + 1, "pointlight", pointLightBprint.name_s, 0, "shit")

    ######## Renderers ########

    @classmethod
    def takeRendererAabBlock(cls, rendererData_l:list, startLineIndex_i:int) -> bp.RendererBlueprint:
        renBprint = bp.RendererBlueprint()

        accumKeyword_l = []
        accumBlock_l = []

        for x, x_l in enumerate(rendererData_l):
            accumLine_l = []
            lineIndex_i = x + startLineIndex_i

            for y_s in x_l:
                if y_s == ";":  # Found a function
                    try:
                        funcName_s, args_s = "".join(accumKeyword_l).split('(')
                    except ValueError:
                        raise CompileErrorSmll( lineIndex_i + 1, "renderer", renBprint.name_s, 1, "".join(accumKeyword_l) )

                    accumKeyword_l = []

                    cls.apllyRendererAabFunction(renBprint, funcName_s, args_s, lineIndex_i)
                else:
                    accumKeyword_l.append(y_s)

            if accumLine_l:
                accumBlock_l.append(accumLine_l)

        cls.makeRendererAabNdArray(renBprint, startLineIndex_i)
        cls.checkRendererAab(renBprint, startLineIndex_i)

        return renBprint
    @staticmethod
    def apllyRendererAabFunction(renBprint:bp.RendererBlueprint, funcName_s:str, args_s:str, lineIndex_i:int) -> None:
        if not isinstance(renBprint, bp.RendererBlueprint):
            raise ValueError(type(renBprint))
        args_s = args_s[:-1]
        args_l = args_s.split(',')
        del args_s

        lineNo_i = lineIndex_i + 1

        if funcName_s == "minpos":
            if not len(args_l) == 3:
                raise CompileErrorSmll( lineNo_i, "renderer", renBprint.name_s, 3, "minpos(float, float, float)", args_l)
            try:
                renBprint.minpos_temp = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "minpos(float, float, float)", args_l)
        elif funcName_s == "maxpos":
            if not len(args_l) == 3:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "maxpos(float, float, float)", args_l)
            try:
                renBprint.maxpos_temp = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "maxpos(float, float, float)", args_l)
        elif funcName_s == "initpos":
            if not len(args_l) == 3:
                raise CompileErrorSmll( lineNo_i, "renderer", renBprint.name_s, 3, "initpos(float, float, float)", args_l )
            try:
                renBprint.initPos_t = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll( lineNo_i, "renderer", renBprint.name_s, 3, "initpos(float, float, float)", args_l )
        elif funcName_s == "name":
            if len(args_l) != 1:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "name(str)", args_l)
            renBprint.name_s = str(args_l[0])
        elif funcName_s == "texture":
            if len(args_l) != 1:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "texture(str)", args_l)
            renBprint.textureDir_s = str(args_l[0])
        elif funcName_s == "texverc":
            if len(args_l) != 1:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "texverc(float)", args_l)
            renBprint.textureVerNum_f = float(args_l[0])
        elif funcName_s == "texhorc":
            if len(args_l) != 1:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "texhorc(float)", args_l)
            try:
                renBprint.textureHorNum_f = float(args_l[0])
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "texhorc(float)", args_l)
        elif funcName_s == "shininess":
            if len(args_l) != 1:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "shininess(float)", args_l)
            try:
                renBprint.shininess_f = float(args_l[0])
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "shininess(float)", args_l)
        elif funcName_s == "specstrength":
            if len(args_l) != 1:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "specstrength(float)", args_l)
            try:
                renBprint.specularStrength_f = float(args_l[0])
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "specstrength(float)", args_l)

        else:
            raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 4, funcName_s)
    @staticmethod
    def checkRendererAab(renBprint:bp.RendererBlueprint, startLineIndex_i:int) -> None:
        if renBprint.name_s is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 5, "name")
        elif renBprint.textureDir_s is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 5, "texture")
        elif renBprint.initPos_t is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 5, "initpos")
        elif renBprint.textureVerNum_f is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 5, "texverc")
        elif renBprint.textureHorNum_f is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 5, "texhorc")
        elif renBprint.shininess_f is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 5, "shininess")
        elif renBprint.specularStrength_f is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 5, "specstrength")

        elif renBprint.vertexNdarray is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 6, "VertexNdarray is not generated.")
        elif renBprint.texCoordNdarray is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 6, "TexCoordNdarray is not generated.")
        elif renBprint.normalNdarray is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 6, "NormalNdarray is not generated.")
    @staticmethod
    def makeRendererAabNdArray(rbp:bp.RendererBlueprint, startLineIndex_i:int) -> None:
        try:
            right_f, up_f, near_f = rbp.maxpos_temp
        except TypeError:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", rbp.name_s, 5, "maxpos")
        else:
            rbp.maxpos_temp = None
        try:
            left_f, down_f, far_f = rbp.minpos_temp
        except TypeError:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", rbp.name_s, 5, "minpos")
        else:
            rbp.minpos_temp = None

        rbp.vertexNdarray = np.array( [
            left_f,  up_f, far_f,
            left_f,  up_f, near_f,
            right_f, up_f, near_f,
            left_f,  up_f, far_f,
            right_f, up_f, near_f,
            right_f, up_f, far_f,

            left_f,  up_f,   near_f,
            left_f,  down_f, near_f,
            right_f, down_f, near_f,
            left_f,  up_f,   near_f,
            right_f, down_f, near_f,
            right_f, up_f,   near_f,

            right_f, up_f, near_f,
            right_f, down_f, near_f,
            right_f, down_f, far_f,
            right_f, up_f, near_f,
            right_f, down_f, far_f,
            right_f, up_f, far_f,

            right_f, up_f, far_f,
            right_f, down_f, far_f,
            left_f, down_f, far_f,
            right_f, up_f, far_f,
            left_f, down_f, far_f,
            left_f, up_f, far_f,

            left_f, up_f, far_f,
            left_f, down_f, far_f,
            left_f, down_f, near_f,
            left_f, up_f, far_f,
            left_f, down_f, near_f,
            left_f, up_f, near_f,

            right_f, down_f, far_f,
            right_f, down_f, near_f,
            left_f, down_f, near_f,
            right_f, down_f, far_f,
            left_f, down_f, near_f,
            left_f, down_f, far_f
        ], np.float32 )

        rbp.texCoordNdarray = np.array( [
            0, 1,
            0, 0,
            1, 0,
            0, 1,
            1, 0,
            1, 1,

            0, 1,
            0, 0,
            1, 0,
            0, 1,
            1, 0,
            1, 1,

            0, 1,
            0, 0,
            1, 0,
            0, 1,
            1, 0,
            1, 1,

            0, 1,
            0, 0,
            1, 0,
            0, 1,
            1, 0,
            1, 1,

            0, 1,
            0, 0,
            1, 0,
            0, 1,
            1, 0,
            1, 1,

            0, 1,
            0, 0,
            1, 0,
            0, 1,
            1, 0,
            1, 1,
        ], np.float32 )

        rbp.normalNdarray = np.array( [
            0, 1, 0,
            0, 1, 0,
            0, 1, 0,
            0, 1, 0,
            0, 1, 0,
            0, 1, 0,

            0, 0, 1,
            0, 0, 1,
            0, 0, 1,
            0, 0, 1,
            0, 0, 1,
            0, 0, 1,

            1, 0, 0,
            1, 0, 0,
            1, 0, 0,
            1, 0, 0,
            1, 0, 0,
            1, 0, 0,

            0, 0, -1,
            0, 0, -1,
            0, 0, -1,
            0, 0, -1,
            0, 0, -1,
            0, 0, -1,

            -1, 0, 0,
            -1, 0, 0,
            -1, 0, 0,
            -1, 0, 0,
            -1, 0, 0,
            -1, 0, 0,

            0, -1, 0,
            0, -1, 0,
            0, -1, 0,
            0, -1, 0,
            0, -1, 0,
            0, -1, 0,
        ], np.float32 )

    @classmethod
    def takeRendererQuadBlock(cls, rendererData_l:list, startLineIndex_i:int) -> bp.RendererBlueprint:
        renBprint = bp.RendererBlueprint()

        accumKeyword_l = []
        accumBlock_l = []

        for x, x_l in enumerate(rendererData_l):
            accumLine_l = []
            lineIndex_i = x + startLineIndex_i

            for y_s in x_l:
                if y_s == ";":  # Found a function
                    try:
                        funcName_s, args_s = "".join(accumKeyword_l).split('(')
                    except ValueError:
                        raise CompileErrorSmll(lineIndex_i + 1, "renderer", renBprint.name_s, 1, "".join(accumKeyword_l))

                    accumKeyword_l = []

                    cls.apllyRendererQuadFunction(renBprint, funcName_s, args_s, lineIndex_i)
                else:
                    accumKeyword_l.append(y_s)

            if accumLine_l:
                accumBlock_l.append(accumLine_l)

        cls.makeRendererQuadNdArray(renBprint, startLineIndex_i)
        cls.checkRendererQuad(renBprint, startLineIndex_i)

        return renBprint
    @staticmethod
    def apllyRendererQuadFunction(renBprint: bp.RendererBlueprint, funcName_s:str, args_s:str, lineIndex_i:int) -> None:
        if not isinstance(renBprint, bp.RendererBlueprint):
            raise ValueError(type(renBprint))
        args_s = args_s[:-1]
        args_l = args_s.split(',')
        del args_s

        lineNo_i = lineIndex_i + 1

        if funcName_s == "pos00":
            if not len(args_l) == 3:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "pos00(float, float, float)", args_l)
            try:
                renBprint.pos00_temp = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "pos00(float, float, float)", args_l)
        elif funcName_s == "pos01":
            if not len(args_l) == 3:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "pos01(float, float, float)", args_l)
            try:
                renBprint.pos01_temp = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "pos01(float, float, float)", args_l)
        elif funcName_s == "pos10":
            if not len(args_l) == 3:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "pos10(float, float, float)", args_l)
            try:
                renBprint.pos10_temp = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "pos10(float, float, float)", args_l)
        elif funcName_s == "pos11":
            if not len(args_l) == 3:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "pos11(float, float, float)", args_l)
            try:
                renBprint.pos11_temp = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "pos11(float, float, float)", args_l)
        elif funcName_s == "initpos":
            if not len(args_l) == 3:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "initpos(float, float, float)",
                                       args_l)
            try:
                renBprint.initPos_t = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "initpos(float, float, float)",
                                       args_l)
        elif funcName_s == "name":
            if len(args_l) != 1:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "name(str)", args_l)
            renBprint.name_s = str(args_l[0])
        elif funcName_s == "texture":
            if len(args_l) != 1:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "texture(str)", args_l)
            renBprint.textureDir_s = str(args_l[0])
        elif funcName_s == "texverc":
            if len(args_l) != 1:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "texverc(float)", args_l)
            renBprint.textureVerNum_f = float(args_l[0])
        elif funcName_s == "texhorc":
            if len(args_l) != 1:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "texhorc(float)", args_l)
            try:
                renBprint.textureHorNum_f = float(args_l[0])
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "texhorc(float)", args_l)
        elif funcName_s == "shininess":
            if len(args_l) != 1:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "shininess(float)", args_l)
            try:
                renBprint.shininess_f = float(args_l[0])
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "shininess(float)", args_l)
        elif funcName_s == "specstrength":
            if len(args_l) != 1:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "specstrength(float)", args_l)
            try:
                renBprint.specularStrength_f = float(args_l[0])
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 3, "specstrength(float)", args_l)

        else:
            raise CompileErrorSmll(lineNo_i, "renderer", renBprint.name_s, 4, funcName_s)
    @staticmethod
    def checkRendererQuad(renBprint: bp.RendererBlueprint, startLineIndex_i:int) -> None:
        if renBprint.name_s is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 5, "name")
        elif renBprint.textureDir_s is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 5, "texture")
        elif renBprint.initPos_t is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 5, "initpos")
        elif renBprint.textureVerNum_f is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 5, "texverc")
        elif renBprint.textureHorNum_f is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 5, "texhorc")
        elif renBprint.shininess_f is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 5, "shininess")
        elif renBprint.specularStrength_f is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 5, "specstrength")

        elif renBprint.vertexNdarray is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 6,
                                   "VertexNdarray is not generated.")
        elif renBprint.texCoordNdarray is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 6,
                                   "TexCoordNdarray is not generated.")
        elif renBprint.normalNdarray is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", renBprint.name_s, 6,
                                   "NormalNdarray is not generated.")
    @staticmethod
    def makeRendererQuadNdArray(rbp: bp.RendererBlueprint, startLineIndex_i:int) -> None:
        if rbp.pos00_temp is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", rbp.name_s, 5, "pos00")
        elif rbp.pos01_temp is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", rbp.name_s, 5, "pos01")
        elif rbp.pos10_temp is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", rbp.name_s, 5, "pos10")
        elif rbp.pos11_temp is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "renderer", rbp.name_s, 5, "pos11")

        rbp.vertexNdarray = np.array([
            *rbp.pos01_temp,
            *rbp.pos00_temp,
            *rbp.pos10_temp,

            *rbp.pos01_temp,
            *rbp.pos10_temp,
            *rbp.pos11_temp
        ], np.float32)

        rbp.texCoordNdarray = np.array([
            0, 1,
            0, 0,
            1, 0,

            0, 1,
            1, 0,
            1, 1,
        ], np.float32)

        a = mm.Vec4(*rbp.pos10_temp) - mm.Vec4(*rbp.pos00_temp)
        b = mm.Vec4(*rbp.pos01_temp) - mm.Vec4(*rbp.pos00_temp)
        xNor_f, yNor_f, zNor_f = a.cross(b).getXYZ()
        rbp.normalNdarray = np.array([
            xNor_f, yNor_f, zNor_f,
            xNor_f, yNor_f, zNor_f,
            xNor_f, yNor_f, zNor_f,
            xNor_f, yNor_f, zNor_f,
            xNor_f, yNor_f, zNor_f,
            xNor_f, yNor_f, zNor_f,
        ], np.float32)

    ######## Colliders ########

    @classmethod
    def takeColliderAabbBlock(cls, rendererData_l:list, startLineIndex_i:int) -> co.Aabb:
        colBprint = bp.ColliderAabbBlueprint()

        accumKeyword_l = []
        accumBlock_l = []

        for x, x_l in enumerate(rendererData_l):
            accumLine_l = []
            lineIndex_i = x + startLineIndex_i

            for y_s in x_l:
                if y_s == ";":  # Found a function
                    funcName_s, args_s = "".join(accumKeyword_l).split('(')
                    accumKeyword_l = []
                    cls.apllyColliderAabbFunction(colBprint, funcName_s, args_s, lineIndex_i)
                else:
                    accumKeyword_l.append(y_s)

            if accumLine_l:
                accumBlock_l.append(accumLine_l)

        cls.checkColliderAabb(colBprint, startLineIndex_i)
        aabb = cls.makeColliderAabb(colBprint, startLineIndex_i)

        return aabb
    @staticmethod
    def apllyColliderAabbFunction(colBprint:bp.ColliderAabbBlueprint, funcName_s:str, args_s:str, lineIndex_i:int) -> None:
        if not isinstance(colBprint, bp.ColliderAabbBlueprint):
            raise ValueError
        args_s = args_s[:-1]
        args_l = args_s.split(',')
        del args_s

        lineNo_i = lineIndex_i + 1

        if funcName_s == "name":
            if not len(args_l) == 1:
                raise CompileErrorSmll(lineNo_i, "collider", colBprint.name_s, 3, "name(str)", args_l)
            try:
                colBprint.name_s = str( args_l[0] )
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "collider", colBprint.name_s, 3, "name(str)", args_l)
        elif funcName_s == "type":
            for type_s in args_l:
                if type_s == "bounding":
                    colBprint.bounding = True
                elif type_s == "blocking":
                    colBprint.blocking = True
                elif type_s == "trigger":
                    colBprint.trigger = True
                else:
                    raise CompileErrorSmll(lineNo_i, "collider", colBprint.name_s, 3, "type(str)", args_l)
        elif funcName_s == "static":
            if args_l[0] == "true":
                colBprint.static_b = True
            elif args_l[0] == "false":
                colBprint.static_b = False
            else:
                raise CompileErrorSmll( lineNo_i, "collider", colBprint.name_s, 3, "static(bool)", args_l )
        elif funcName_s == "initpos":
            if not len(args_l) == 3:
                raise CompileErrorSmll(lineNo_i, "collider", colBprint.name_s, 3, "initpos(float, float, float)", args_l)
            try:
                colBprint.initPos_t = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "collider", colBprint.name_s, 3, "initpos(float, float, float)", args_l)
        elif funcName_s == "minpos":
            if not len(args_l) == 3:
                raise CompileErrorSmll(lineNo_i, "collider", colBprint.name_s, 3, "minpos(float, float, float)", args_l)
            try:
                colBprint.min_t = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "collider", colBprint.name_s, 3, "minpos(float, float, float)", args_l)
        elif funcName_s == "maxpos":
            if not len(args_l) == 3:
                raise CompileErrorSmll(lineNo_i, "collider", colBprint.name_s, 3, "maxpos(float, float, float)", args_l)
            try:
                colBprint.max_t = tuple(map(lambda xx:float(xx), args_l))
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "collider", colBprint.name_s, 3, "maxpos(float, float, float)", args_l)
        elif funcName_s == "command":
            colBprint.triggerCommand_l += args_l
        elif funcName_s == "weight":
            if not len(args_l) == 1:
                raise CompileErrorSmll(lineNo_i, "collider", colBprint.name_s, 3, "weight(float)", args_l)
            try:
                colBprint.weight_f = float( args_l[0] )
            except ValueError:
                raise CompileErrorSmll(lineNo_i, "collider", colBprint.name_s, 3, "weight(float)", args_l)
        elif funcName_s == "activateoption":
            if len(args_l) != 1:
                raise CompileErrorSmll(lineNo_i, "collider", colBprint.name_s, 3, "activateoption(str)", args_l)
            elif args_l[0] == "once":
                colBprint.activateOption_i = 1
            elif args_l[0] == "toggle":
                colBprint.activateOption_i = 2
            elif args_l[0] == "press":
                colBprint.activateOption_i = 3
            else:
                raise CompileErrorSmll(lineNo_i, "collider", colBprint.name_s, 3, "activateoption(str)", args_l)
        else:
            raise CompileErrorSmll(lineNo_i, "collider", colBprint.name_s, 4, funcName_s)
    @staticmethod
    def checkColliderAabb(colBprint:bp.ColliderAabbBlueprint, startLineIndex_i:int) -> None:
        if colBprint.name_s is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "collider", colBprint.name_s, 5, "name")
        elif all( (not colBprint.trigger, not colBprint.blocking, not colBprint.bounding) ):
            raise CompileErrorSmll(startLineIndex_i + 1, "collider", colBprint.name_s, 5, "type")
        elif colBprint.trigger and len(colBprint.triggerCommand_l) == 0:
            raise CompileErrorSmll(startLineIndex_i + 1, "collider", colBprint.name_s, 5, "command")
        elif colBprint.initPos_t is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "collider", colBprint.name_s, 5, "initpos")
        elif colBprint.weight_f is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "collider", colBprint.name_s, 5, "weight")
        elif colBprint.static_b is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "collider", colBprint.name_s, 5, "static")
        elif colBprint.min_t is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "collider", colBprint.name_s, 5, "minpos")
        elif colBprint.max_t is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "collider", colBprint.name_s, 5, "maxpos")
        elif colBprint.activateOption_i is None:
            raise CompileErrorSmll(startLineIndex_i + 1, "collider", colBprint.name_s, 5, "activateoption")
    @staticmethod
    def makeColliderAabb(colBprint:bp.ColliderAabbBlueprint, startLineIndex_i:int) -> co.Aabb:
        colBprint.triggerCommand_l.reverse()
        return co.Aabb(
            colBprint.min_t, colBprint.max_t, colBprint.name_s, colBprint.weight_f, colBprint.initPos_t,
            colBprint.static_b, colBprint.bounding, colBprint.blocking, colBprint.trigger, colBprint.triggerCommand_l,
            colBprint.activateOption_i
        )


    @staticmethod
    def checkNameDuplicate(level:ds.Level) -> None:
        names_l = []
        for anObject in level.objectBlueprints_l:
            if anObject.name_s == "unknown":
                continue
            elif anObject.name_s in names_l:
                raise CompileErrorSmll(0, "", level.getName(), 7, anObject.name_s)
            else:
                names_l.append(anObject.name_s)

        for anObject in level.objectBlueprints_l:
            names_l = []
            try:
                renderBprints_l = anObject.rendererBlueprints_l
            except AttributeError:
                continue
            else:
                for anRenderer in renderBprints_l:
                    if anRenderer.name_s == "unknown":
                        continue
                    elif anRenderer.name_s in names_l:
                        raise CompileErrorSmll(0, "", level.getName(), 7, anRenderer.name_s)
                    else:
                        names_l.append(anRenderer.name_s)


def main():
    levelParser = SmllCompiler("C:\\Users\\sungmin\\OneDrive\\Programming\\Python\\3.5\\escapeRoom\\assets\levels\\entry.smll")
    level = levelParser.compile()


if __name__ == '__main__':
    main()
