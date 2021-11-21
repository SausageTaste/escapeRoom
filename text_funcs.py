

def getTextSimilarity(from_s:str, target_s:str):
    score_i = 0

    for x in range(len(from_s)-1):
        if target_s.count(from_s[x:x+2]):
            score_i += 4
    for x in range(len(from_s)-2):
        if target_s.count(from_s[x:x+3]):
            score_i += 9

    return score_i


def main():
    a = getTextSimilarity("are you fucking kidding me", "im not kidding")
    print(a)
    a = getTextSimilarity("are you fucking kidding me", "that sucks man jesus christ")
    print(a)


if __name__ == '__main__':
    main()
