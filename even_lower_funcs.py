import os
from xml.etree import cElementTree as ET


def create_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)


def get_text(xml_path):
    # === open and read out text of xml file ===
    tree = ET.parse(xml_path)
    root = tree.getroot()

    return ET.tostring(root.find("TEXT"), encoding="unicode", method="xml")

def find_name_start(condition, text, strt_brkt, i):
    if condition:
        x = 2
        while text[strt_brkt - i + x].isspace():
            x += 1
        strt_brkt = strt_brkt - i + x  # start of name
        return True
    return False


def find_word_end(text, idx):
    DEBUG = False

    i = 0
    # while the situation does not appear that a certain index is a letter and the next one is not anymore:
    while not ((text[idx+i].islower() or text[idx+i].isupper()) and not (text[idx+i+1].islower() or text[idx+i+1].isupper())):
        i += 1
    if DEBUG: print("Word End: ", text[idx:idx+i+1])
    return idx+i+1


def find_word_start(text, idx):
    DEBUG = False

    i = 0
    while not ((text[idx - i].islower() or text[idx - i].isupper()) and text[idx-i-1].isspace()):
        i += 1

    end_idx = find_word_end(text, idx-i)
    if DEBUG: print("Word Start: ", text[idx-i:end_idx])
    return idx - i


def get_word_idc(text, idx):
    DEBUG = False

    start_idx = find_word_start(text, idx)

    end_idx = find_word_end(text, start_idx)
    if DEBUG: print("Word: ", text[start_idx:end_idx])
    return start_idx, end_idx


def crop_text(minutes_text):

    DEBUG = False
    DEBUG_while = False

    fail = False

    # === Remove unnecessary content before debates
    # (marked by "Die Sitzung ist eröffnet") ===
    start_idx = minutes_text.find("Sitzung ist eröffnet")
    start_idx_2 = minutes_text.find("ist eröffnet")  # da es vorkommt, dass Sitzung am blattrand aufgeteilt war
    start_idx_3 = minutes_text.find("ich eröffne")
    start_idx_4 = minutes_text.find("für eröffnet")
    start_idx_5 = minutes_text.find("Ich eröffne")
    start_idx_6 = minutes_text.find("Sitzung des Bundestags der Bundesrepublik Deutschland für eröffnet")
    
    if not (max(start_idx, start_idx_2, start_idx_3, start_idx_4, start_idx_5, start_idx_6) > 0):
        print("Sitzung Start Error")
        fail = True
        return "", fail

    idc = [start_idx, start_idx_2, start_idx_3, start_idx_4, start_idx_5, start_idx_6]

    while min(idc) == -1:
        if DEBUG_while: print("while1")
        idc.remove(min(idc))

    start_idx = min(idc)

    # === find last sitzung "Die Sitzung ist geschlossen" or "ich schliesse die Sitzung" or whatever
    start = 0
    sitzung_idc = []
    sitzung_idx = 0
    idx = 1

    if DEBUG: print("HELLO")

    # === Find first occurence of " Sitzung" ===
    while idx > 0:
        if DEBUG_while: print("while2")
        idx = minutes_text.find(" Sitzung", start)
        assert (idx != -1)

        if minutes_text[idx - 1] != "." and minutes_text[idx + 8] != ":":
            sitzung_idx = idx
            break

        start = idx + 1

    if DEBUG: print("HELLO 2")

    # END INDEX

    end_idx = 10000000
    end_start = len(minutes_text)

    while end_idx == 10000000:
        if DEBUG_while: print("while3")
        if DEBUG: print("Start")
        temp_idx = minutes_text.rfind("Schluss", 0, end_start)
        temp_idx_2 = minutes_text.rfind("Schluß", 0, end_start)

        idx = max(temp_idx, temp_idx_2)

        if DEBUG: print(minutes_text.find(")", idx), idx, minutes_text.find(")", idx) - idx)
        if DEBUG: print(idx, minutes_text.rfind("(", 0, idx), idx - minutes_text.rfind("(", 0, idx))

        if minutes_text.find(")", idx) > 0:
            if minutes_text.rfind("(", 0, idx) > 0:
                if minutes_text.find(")", idx) - idx < 70 and idx - minutes_text.rfind("(", 0, idx) < 20:
                    if DEBUG: print("found")
                    end_idx = idx - 1
                    break

        if DEBUG: print("not found")
        end_start = idx

        if DEBUG: print(end_start)

    if not ("Anlage 1\n" not in minutes_text[start_idx:end_idx]) or not ("Analge 1 zum" not in minutes_text[start_idx:end_idx]):
        print("Cropping Error, Anlage 1 still in text")
        fail = True
        return "", fail

    # assert("Anlage 1\n" not in minutes_text[start_idx:end_idx])
    # assert("Analge 1 zum" not in minutes_text[start_idx:end_idx])

    if DEBUG: print("Text Length: " + str(len(minutes_text)) + " start: " + str(start_idx) + " end: " + str(end_idx)
                    + " Text Length cropped: " + str(len(minutes_text[start_idx:end_idx])))

    test_1 = 0
    if not start_idx - 70 < 0:
        test_1 -= 70
    else:
        test_1 = start_idx

    test_2 = 0

    search_start = start_idx
    temp_idx_2 = minutes_text.rfind(":", 0, search_start)

    while not temp_idx_2 - minutes_text.rfind("räsident", 0, temp_idx_2) < 40 and not minutes_text[find_word_start(minutes_text, temp_idx_2-1)].isupper():
        if DEBUG_while: print("while4")
        search_start = temp_idx_2 - 1
        temp_idx_2 = minutes_text.rfind(":", 0, search_start)
        if DEBUG: print(minutes_text[find_word_start(minutes_text, temp_idx_2-1)-1])
        if DEBUG: print(minutes_text[find_word_start(minutes_text, temp_idx_2-1)])
        if DEBUG: print(minutes_text[find_word_start(minutes_text, temp_idx_2-1)+1])



    temp_idx_2 -= 40

    if not temp_idx_2 == -1:
        test_2 = temp_idx_2

    start_idx = max(test_1, test_2)

    return minutes_text[start_idx:end_idx], fail


def get_first_speaker(speaker_names, text, date_end_idx):
    DEBUG = False

    temp_idx_speaker = 1000000

    # === Add all speakers indices that appear after the date end ===
    idc_arr = []
    for speaker in speaker_names:
        if DEBUG: print("find speaker: ", speaker)
        temp_idx = text.find(speaker, date_end_idx)
        if temp_idx != -1:
            idc_arr.append(temp_idx)
            if DEBUG: print("adding index")

    # === remove all indices smaller than date_end_idx as long as there are 2 left so that 1 can be removed ===
    # e.g. if a bundesminister holds a long speech that fills the page --> no speakers found
    while len(idc_arr) > 1 and min(idc_arr) <= date_end_idx:  # were only looking for speakers after the date index
        idc_arr.remove(min(idc_arr))
        if DEBUG: print("remove index")

    # === if the array is not empty give out the minimum ===
    if len(idc_arr) > 0:
        temp_idx_speaker = min(idc_arr)

    if DEBUG: print("speaker index and speaker: ", temp_idx_speaker, text[temp_idx_speaker:temp_idx_speaker+40])

    return temp_idx_speaker


def get_part_of_tuples(speaker_party_speech_idc, index):
    array = []
    for i in range(len(speaker_party_speech_idc)):
        speaker_idx, speaker_name, party, speech_strt_idx = speaker_party_speech_idc[i]
        if index == 1:
            array.append(speaker_idx)
        elif index == 2:
            array.append(speaker_name)
        elif index == 3:
            array.append(party)
        elif index == 4:
            array.append(speech_strt_idx)
        else:
            print("Error, index not in range")
    return array


def get_speaker_continued_speech(speaker_names, text):
    DEBUG = False

    # TODO: 03002 Gerstenmaier name in the middle of the speech not removed

    speaker_idc = []
    start = 0

    for i in range(len(speaker_names)):
        idx = text.find(speaker_names[i], start)
        while idx > 0:
            before_idx = idx - 1
            after_idx = idx + len(speaker_names[i]) + 1

            # if DEBUG: print(before_idx, after_idx)
            # if DEBUG: print(text[before_idx - 5:after_idx + 5] + "\n")

            if text[before_idx] == "\n" and text[after_idx-1] == "\n":

                if DEBUG: print(text[before_idx - 5:after_idx + 5] + "\n")

                speaker_idc.append((before_idx, after_idx))

            start = idx + 1
            idx = text.find(speaker_names[i], start)

    return speaker_idc