import os
from even_lower_funcs import *

Parteien = ("CDU", "SPD", "CDU/CSU", "FDP", "DP", "FU", "BP", "KPD", "WAV", "FRAKTIONSLOS", "GB/BHE", "ZENTRUM", "DIE GRÜNEN", "BÜNDNIS 90/DIE GRÜNEN", "PDS", "DIE LINKE.", "DIE LINKE", "UNABHÄNGIG", "AFD", "GRÜNE")
minutes_path = "/Users/nektarioswinter/Documents/PoliticianProject/protokolle/"
xml_path = ""


def write_txt_file(path, text, verbose):
    textfile = open(path, "w+")
    textfile.write(text)
    textfile.close()
    if verbose: print("Text file: " + path + " saved!")


def delete_file(filename, id, verbose):
    files_dir = minutes_path + id[:2] + "/" + id + "/"
    path = files_dir + id + "-" + filename + ".txt"
    os.remove(path)
    if verbose: print("Removed file: ", path)


def create_dirs(id, verbose, save_files):

    global xml_path

    # === manage paths and directories ===
    xml_path = minutes_path + "pp" + id[:2] + "-data/" + id + ".xml"

    if not save_files:
        return True

    if os.path.exists(xml_path):

        create_dir(minutes_path + id[:2] + "/")
        create_dir(minutes_path + id[:2] + "/" + id)

        if verbose: print("Directories OK!")
        return True

    else:
        if verbose: print("No xml file found for " + id + "!")
        return False


def file_exists(id, verbose, path, file):
    for root, dirnames, filenames in os.walk(path):
        for filename in filenames:
            if filename == id + file:
                if verbose: print(id + file + " already saved!")
                return True
    return False


def remove_all_files(id, verbose, path):
    # fuck my life what am i doing and why does this even work
    for root, up_dirnames, filenames in os.walk(path):
        for up_dirname in up_dirnames:
            if up_dirname == id[:2]:
                for root, dirnames, filenames in os.walk(path + up_dirname):
                    for dirname in dirnames:
                        if dirname == id:
                            for filename in filenames:
                                if "DS_Store" not in filename:
                                    os.remove(path + dirname + "/" + filename)
    if verbose: print("Folder for " + id + " removed!")


def xml_to_txt(id, verbose, save_files):
    global xml_path

    # === extract text from file ===
    minutes_text = get_text(xml_path)

    # === Remove <TEXT> and </TEXT> ===
    minutes_text = minutes_text[6:len(minutes_text) - 8]

    # === write text in txt file ===
    txt_path = minutes_path + id[:2] + "/" + id + "/" + id + "-ultra_raw.txt"

    if save_files:
        write_txt_file(txt_path, minutes_text, verbose)

    # === remove unnecessary start and end part ===
    minutes_text, fail = crop_text(minutes_text)

    if len(minutes_text) < 1000:
        print("Conversion Error, detected text too short")
        return False, " ", fail  # return not successful

    # === write text in txt file ===
    txt_path = minutes_path + id[:2] + "/" + id + "/" + id + "-raw.txt"

    if save_files:
        write_txt_file(txt_path, minutes_text, verbose)
        if verbose: print("Saved " + str(id) + " as .txt file!")
        return True, " ", fail
    else:
        return True, minutes_text, fail


def text_is_party(text, strt_brkt, end_brkt):
    return text[strt_brkt + 1:end_brkt:].upper() in Parteien and (
            text[end_brkt + 2] == ":" or text[end_brkt + 1] == ":")


def remove_text(text, strt_brkt, end_brkt, DEBUG):
    if DEBUG: print("Text between brackets removed: " + text[strt_brkt + 1:end_brkt] + "\n")  # print what is removed
    text = text[:strt_brkt] + text[end_brkt + 1:]  # remove text between brackets
    return text


def get_speaker_and_party(text, strt_brkt):
    DEBUG_1 = False
    DEBUG_2 = False

    # === extract speaker name and party ===
    speaker_start_idx, speaker_end_idx = get_word_idc(text, strt_brkt-2)
    speaker = text[speaker_start_idx:speaker_end_idx]
    party = text[text.find("(", speaker_start_idx) + 1:text.find(")", speaker_start_idx)]

    if DEBUG_2: print(speaker)
    if DEBUG_1: print("Speaker: ", speaker_start_idx)

    return speaker, speaker_start_idx, party


def get_speech_strt_idx(text, end_brkt):
    DEBUG = False

    for i in range(5):
        if DEBUG: print(text[end_brkt:end_brkt + 10])
        if DEBUG: print(text[end_brkt+i-1:end_brkt+i+1])

        if (text[end_brkt + i].isupper() and text[end_brkt + i - 1].isspace()) or \
                ("– " in text[end_brkt+i-1:end_brkt+i+2]):
            speech_start_idx = end_brkt + i  # === add the index of the first letter of the speech ===

            if DEBUG: print("Speaker Speech Start Index: ", speech_start_idx)

            return speech_start_idx, False
    return 0, True


def remove_title(speaker, title, DEBUG):

    start_idx = speaker.find(title)
    end_idx = start_idx + len(title)
    if start_idx >= 0:
        speaker = speaker[:start_idx] + speaker[end_idx:]
        if DEBUG: print('Without "' + title + '" : ' + speaker)
    return speaker


def remove_titles(speaker_name, DEBUG):
    speaker_name = remove_title(speaker_name, "Dr. ", DEBUG)
    speaker_name = remove_title(speaker_name, "Dr ", DEBUG)
    speaker_name = remove_title(speaker_name, "Herr ", DEBUG)
    speaker_name = remove_title(speaker_name, "Frau ", DEBUG)
    speaker_name = remove_title(speaker_name, "Graf ", DEBUG)
    speaker_name = remove_title(speaker_name, "Freiherr ", DEBUG)

    return speaker_name


def get_name(speaker):
    # === Extract each speakers name ===
    name_end_idx = speaker.find("(") - 2
    if speaker[speaker.find("(") - 2].islower():
        name_end_idx += 1
    return speaker[:name_end_idx]


def is_faulty(speaker_name, DEBUG):
    # === remove faulty names (e.g. "(FD" ) ===
    if speaker_name.find("(") >= 0:
        if DEBUG: print("Removed: " + speaker_name)
        return True


def two_consec_numbers(text, idx, DEBUG):
    # === if there are 2 consecutive numbers before ===
    if text[idx - 2].isnumeric() and text[idx - 3].isnumeric():
        if DEBUG: print("Found the numbers")
        return True
    return False


def get_page_end_idx(text, bundestag_idx, cnt):

    DEBUG = False
    DEBUG_fine = False

    flag = 1

    # === check how many numbers there are, if we reach the end
    # --> end of previous page (only on uneven pages (right half) ===
    for i in range(5):
        test_idx = bundestag_idx - (3 + i)
        if text[test_idx].isnumeric():
            if DEBUG_fine: print("Index #" + str(test_idx) + " is still numeric")
            continue

        else: # text[test_idx].isspace():

            # ################=== end of page found ===################
            page_end = test_idx
            if DEBUG: print("End of page #" + str(cnt) + " found: " + str(page_end))
            assert(page_end is not None)

            flag = 0
            return page_end  # page_end_idx

    assert(flag == 0)


def get_date_end_idx(id, text, idx):

    # === find the index of the date on the header ===
    # (since 19 and 20 could be day dates, make sure its followed by a number)
    # later to find the name of the speaker right after it

    # TODO: finish for wahlperiode 14, since both 19xx and 20xx
    # TODO: split into smaller functions in even_smaller_funcs.py

    DEBUG = False

    end_date_idx = 0
    if int(id[:2]) < 14:
        while (1):
            date_idx_19 = text.find("19", idx)
            if not text[date_idx_19 + 1] == ".":
                if DEBUG: print("FOUND YEAR: " + text[date_idx_19:date_idx_19 + 4])
                end_date_idx = date_idx_19 + 4
                if DEBUG: print("FOUND Index end of the year: " + str(end_date_idx))
                break
            pass

    elif int(id[:2]) > 14:
        while (1):
            date_idx_20 = text.find("20", idx)
            if not text[date_idx_20 + 1] == ".":
                if DEBUG: print("FOUND YEAR: " + text[date_idx_20:date_idx_20 + 4])
                end_date_idx = date_idx_20 + 4
                if DEBUG: print("FOUND Index end of the year: " + str(end_date_idx))
                break
            pass

    return end_date_idx


def get_page_start_idx(speaker_names, date_end_idx, text):
    # === figure out the index of the page start after the top name===

    DEBUG = False

    page_start_idx = 1000000  # something random high

    if DEBUG: print("date end index: " + str(date_end_idx))

    if DEBUG: print(len(speaker_names))
    assert(len(speaker_names) >= 0)

    # === Add the first speakers index that appears after the date end ===
    temp_idx_speaker = get_first_speaker(speaker_names, text, date_end_idx)
    if temp_idx_speaker <= 0:
        temp_idx_speaker = 1000000
    # === look for the smallest indices of "Bundes" and "räsident" in case any minister or president talks ===
    temp_idx_bundes = text.find("Bundes", date_end_idx)
    if temp_idx_bundes <= 0:
        temp_idx_bundes = 1000000
    # could be Präsident or Vizepräsident ... P could be capital or not
    temp_idx_president = text.find("räsident", date_end_idx)
    if temp_idx_president <= 0:
        temp_idx_president = 1000000


    smallest_temp = min(temp_idx_speaker, temp_idx_bundes, temp_idx_president)

    # === depending on which occurs first, set that to be top_name_idx ===
    if smallest_temp == temp_idx_speaker:
        page_start_idx = text.find("\n", temp_idx_speaker) + 1
        if DEBUG: print("Page Start(speaker):", page_start_idx, text[page_start_idx:page_start_idx+30])

    elif smallest_temp == temp_idx_bundes:  # Falls kein speaker sondern ein Minister redet -->
        page_start_idx = text.find("\n", temp_idx_bundes) + 1
        if DEBUG: print("Page Start(bundes):", page_start_idx, text[page_start_idx:page_start_idx+30])

    elif smallest_temp == temp_idx_president:
        page_start_idx = text.find("\n", temp_idx_president) + 1
        if DEBUG: print("Page Start(präsident):", page_start_idx, text[page_start_idx:page_start_idx+30])


    if DEBUG: print("\n")

    if page_start_idx == 1000000:
        if DEBUG: print("couldnt find speaker, Bundes or Präsident at start")  # just connect pages after date or

        if text[date_end_idx + 2].isnumeric() and text[date_end_idx + 3].isnumeric():
            page_start_idx = text.find("\n", date_end_idx+2)
        else:
            page_start_idx = text.find("\n", date_end_idx)


    return page_start_idx


def get_speech_end_idc(text, speaker_party_speech_idc, verbose):

    # == find first "." before speaker_idx that is not "Dr." or "D." (an error) or "Prof." ===

    speech_end_idc = []
    speech_end_idx = 0
    DEBUG = False

    for i in range(len(speaker_party_speech_idc)-1):
        found = False
        old_speaker_idx, old_speaker_name, old_party, old_speech_strt_idx = speaker_party_speech_idc[i]
        speaker_idx, speaker_name, party, speech_strt_idx = speaker_party_speech_idc[i+1]
        start = speaker_idx

        # assert(text[speaker_idx].isupper())

        while found is False:
            if DEBUG: print("Old speech start, old speaker indices: ", old_speech_strt_idx, start, old_speaker_idx)

            assert(type(old_speech_strt_idx) == int)

            if DEBUG: print("Start of Speech: ", text[old_speech_strt_idx:old_speech_strt_idx+40])
            if DEBUG: print("End of Speech: ", text[start-5:start+5])

            idx1 = text.rfind(".", old_speech_strt_idx-2, start)
            idx2 = text.rfind("–", old_speech_strt_idx-2, start)
            idx3 = text.rfind("!", old_speech_strt_idx-2, start)
            idx4 = text.rfind("?", old_speech_strt_idx-2, start)
            idx5 = text.rfind("\n", old_speech_strt_idx-2, start)
            idx = max(idx1, idx2, idx3, idx4, idx5)

            # print(idx1, idx2, idx3, idx4, idx)

            if idx > 0:
                # print(idx)
                if not ("Dr" in text[idx-2:idx] or "D" in text[idx-1:idx] or "Prof" in text[idx-4:idx] or
                        " h" in text[idx-2:idx] or " c" in text[idx-2:idx]):
                    if DEBUG: print("FOUND!")
                    if DEBUG: print("manually check for titles: ", text[idx - 15:idx])
                    found = True
                    speech_end_idx = idx + 1
                else:
                    if DEBUG: print("Not found!")
                    start = idx - 1
            else:
                # print("HOW DID I GET HERE", text[old_speech_strt_idx-2:start+2])
                # print("End of Speech: ", text[start - 5:start + 5])
                if verbose: print("Speech Start/End Recognition FAIL 1!")
                return True, []

        if found:
            if DEBUG: print("old speech start, speech end indices: ", old_speech_strt_idx, speech_end_idx)
            if DEBUG: print("\n")

            assert(speaker_idx >= speech_end_idx)

            #assert(old_speech_strt_idx < speech_end_idx)
            if not old_speech_strt_idx < speech_end_idx:
                if verbose: print("Speech Start/End Recognition FAIL 2!")
                return True, []

            speech_end_idc.append(speech_end_idx)

    speech_end_idc.append(len(text))

    return False, speech_end_idc


def get_text_from_file(filename, id):
    # === Open and Read No Bracket File ===
    files_dir = minutes_path + id[:2] + "/" + id + "/"
    textfile = open(files_dir + id + "-" + filename + ".txt", "r")
    text = textfile.read()
    return text


def add_page_end_idx(text, bundestag_idx, cnt):
    DEBUG = False

    # uneven pages have 3/4 digit number in front of "Deutscher Bundestag"
    if two_consec_numbers(text, bundestag_idx, DEBUG):
        page_end_idx = get_page_end_idx(text, bundestag_idx, cnt)
    # even pages dont
    else:
        page_end_idx = bundestag_idx - 1

    if DEBUG: print("Page End Index: " + str(page_end_idx) + "\n")
    return page_end_idx


def add_page_start_idx(text, bundestag_idx, speaker_names, id):
    DEBUG = False

    date_end_idx = get_date_end_idx(id, text, bundestag_idx)
    # if DEBUG: print("Date End Index: " + str(date_end_idx))

    page_start_idx = get_page_start_idx(speaker_names, date_end_idx, text)
    if DEBUG: print("\nPage Start Index:", page_start_idx, "\n")

    return page_start_idx


def debugs_and_asserts(DEBUG, page_start_idc, page_end_idc, text):

    DEBUG = False
    fail = False

    # ##########=== DEBUG/ASSERTS ===##########
    if DEBUG: print("START INDICES:", page_start_idc)
    if DEBUG: print("\nEND INDICES:", page_end_idc)

    # assert (len(page_start_idc) == len(page_end_idc))
    if not (len(page_start_idc) == len(page_end_idc)):
        if DEBUG: print("Length of page start idc:", len(page_start_idc))
        if DEBUG: print("Length of page end idc:", len(page_end_idc))
        fail = True
    for i in range(len(page_start_idc) - 1):
        # assert (page_start_idc[i] < page_start_idc[i + 1])
        if not (page_start_idc[i] < page_start_idc[i + 1]):
            if DEBUG: print("Page Start i and i+1:", page_start_idc[i], page_start_idc[i + 1])
            if DEBUG: print("Text from Start i and i+1:", text[page_start_idc[i]:page_start_idc[i]+15], "   ", text[page_start_idc[i+1]:page_start_idc[i+1]+15])
            fail = True
        # assert (page_end_idc[i] < page_end_idc[i + 1])
        if not (page_end_idc[i] < page_end_idc[i + 1]):
            if DEBUG: print("Page End i and i+1:", page_end_idc[i], page_end_idc[i + 1])
            if DEBUG: print("Text from End i and i+1:", text[page_end_idc[i]:page_end_idc[i]+15], "   ", text[page_end_idc[i+1]:page_end_idc[i+1]+15])
            fail = True
        # assert (page_start_idc[i] < page_end_idc[i + 1])
        if not (page_start_idc[i] < page_end_idc[i + 1]):
            if DEBUG: print("Page Start i and Page End i+1:", page_start_idc[i], page_end_idc[i + 1])
            if DEBUG: print("Text from Start i and Page End i+1:", text[page_start_idc[i]:page_start_idc[i]+15], "   ", text[page_end_idc[i+1]:page_end_idc[i+1]:15])
            fail = True

    return fail


def get_pure_text(DEBUG, page_start_idc, page_end_idc, text, test_page):
    pure_text = ""
    if test_page:
        if DEBUG: print("Start Indices: " + str(page_start_idc))
        if DEBUG: print("End Indices: " + str(page_end_idc))
        pure_text = text[page_start_idc[0]:page_end_idc[0]] + "##############" + text[page_start_idc[1]:page_end_idc[1]]
    else:
        for page in range(len(page_start_idc)):
            pure_text += text[page_start_idc[page]:page_end_idc[page]]

            if pure_text[-1] == "-" and pure_text[-2].islower():
                pure_text = pure_text[:-1]  # TEST
            else:
                pure_text += " "

            if DEBUG: pure_text += "#########################"  # to make the page ends visible

    return pure_text


def get_bundes_speakers(text):

    DEBUG_1 = False
    DEBUG_2 = False

    # ######=== Find all ministers ===#######
    start = 0
    bundes_speakers = []
    start_idc = []
    bundes_idx = text.find("Bundes")
    while bundes_idx > 0:

        test_idx_1 = text.find("minister", bundes_idx) - bundes_idx
        test_idx_2 = text.find("kanzler", bundes_idx) - bundes_idx

        def cond(test_idx):
            if 0 < test_idx < 30:
                return True
            return False

        end_idx = find_word_end(text, bundes_idx)

        # komma vor bundesminister
        cond_3 = text[bundes_idx - 2] == ","

        # if DEBUG: print(cond(test_idx_1-bundes_idx) or cond(test_idx_2-bundes_idx), cond_3, cond_4)

        # falls entweder minister oder kanzler und komma davor
        if (cond(test_idx_1) or cond(test_idx_2)) and cond_3:

            name_start_idx = find_word_start(text, bundes_idx - 2)
            if DEBUG_1: print("Bundes: ", name_start_idx)

            if text[name_start_idx - 4:name_start_idx - 1] == "von" or text[
                                                                       name_start_idx - 3:name_start_idx - 1] == "zu":
                name_start_idx = find_word_start(text, name_start_idx - 3)

            name_end_idx = bundes_idx - 2
            if DEBUG_2: print("Name End: ", name_end_idx)

            if DEBUG_2: print("Text: " + text[name_start_idx:name_end_idx])
            bundes_speakers.append(text[name_start_idx:name_end_idx])
            start_idc.append(name_start_idx)

        start = bundes_idx + 1
        bundes_idx = text.find("Bundes", start)

    return bundes_speakers, start_idc


def get_pres_speakers(text):
    DEBUG_1 = False
    DEBUG_2 = False

    presidents = []
    start_idc = []

    # ######=== Find all presidents ===#######
    start = 0
    pres_idx = text.find("räsident", start)

    # solange "räsident" vorkommt
    while pres_idx > 0:

        # falls unmittelbar danach ":"
        temp_idx = text.find(":", pres_idx)
        if temp_idx - pres_idx < 40 and temp_idx > 0:

            name_start_idx = find_word_start(text, temp_idx - 1)

            #if name_start_idx > 0:
            name_end_idx = temp_idx

            assert(name_start_idx < name_end_idx)
            if DEBUG_1: print("Präsident: ", name_start_idx, name_end_idx)

            president = text[name_start_idx:name_end_idx]
            if DEBUG_2: print("Präsident: ", president)

            presidents.append(president)
            start_idc.append(name_start_idx)

        start = pres_idx + 1
        pres_idx = text.find("räsident", start)

    return presidents, start_idc


def get_bundes_pres_speech_strt(text, speaker_idx):
    # === look for first ":" or first line break ===
    DEBUG = False

    start = speaker_idx
    while text[start] != ":" and text[start] != "\n":
        if ":" not in text[start:start+15]:
            start += 1
        else:
            start = text.find(":", start)
    strt = start
    while not text[strt].isupper():
        strt += 1

    assert(type(strt) == int)
    assert(strt > 0)

    if DEBUG: print("Bundes/Pres Speech Start Idx: ", strt)

    return strt


def get_secr_speakers(text):

    DEBUG_1 = False
    DEBUG_2 = False

    secretaries = []
    start_idc = []

    # ######=== Find all secretaries ===#######
    start = 0
    sec_idx = text.find("Staatssekretär", start)

    # solange "sekretär" vorkommt
    while sec_idx > 0:

        # falls unmittelbar danach ":"
        temp_idx = text.find(":", sec_idx)
        temp_idx_2 = text.rfind(",", 0, sec_idx)

        if temp_idx - sec_idx < 40 and temp_idx > 0 and sec_idx - temp_idx_2 < 10:

            name_start_idx = find_word_start(text, temp_idx_2 - 2)

            # if name_start_idx > 0:
            name_end_idx = temp_idx_2

            assert (name_start_idx < name_end_idx)
            if DEBUG_1: print("Sekretär: ", name_start_idx, name_end_idx)

            secretary = text[name_start_idx:name_end_idx]
            if DEBUG_2: print("Sekretär: ", secretary)

            secretaries.append(secretary)
            start_idc.append(name_start_idx)

        start = sec_idx + 1
        sec_idx = text.find("sekretär", start)

    return secretaries, start_idc


def get_schrift_speakers(text):

    # like bundes/pres/secretaries this function finds Schriftführer (e.g. 02022)

    DEBUG = False

    schrifts = []
    start_idc = []

    # ######=== Find all Schriftführer ===#######
    start = 0
    schrift_idx = text.find("Schriftführer", start)

    if schrift_idx == -1:
        if DEBUG: print("Kein Schriftführer gefunden")

    # solange "schriftführer" vorkommt
    while schrift_idx > 0:

        # falls unmittelbar danach ":"
        temp_idx = text.find(":", schrift_idx)
        temp_idx_2 = text.rfind(",", 0, schrift_idx)

        if temp_idx - schrift_idx < 20 and temp_idx > 0 and schrift_idx - temp_idx_2 < 10:

            name_start_idx = find_word_start(text, temp_idx_2 - 2)

            # if name_start_idx > 0:
            name_end_idx = temp_idx_2

            assert (name_start_idx < name_end_idx)
            # if DEBUG: print("Schriftführer: ", name_start_idx, name_end_idx)

            schrift = text[name_start_idx:name_end_idx]
            if DEBUG: print("Schriftführer: ", schrift)

            schrifts.append(schrift)
            start_idc.append(name_start_idx)

        start = schrift_idx + 1
        schrift_idx = text.find("Schriftführer", start)

    return schrifts, start_idc


def get_anfragender_speakers(text):

    # like bundes/pres/secretaries this function finds Schriftführer (e.g. 02022)

    DEBUG = False

    anfrags = []
    start_idc = []

    # ######=== Find all Schriftführer ===#######
    start = 0
    anfrag_idx = text.find("Anfragende", start)

    if anfrag_idx == -1:
        if DEBUG: print("Keinen Anfragenden gefunden")

    # solange "schriftführer" vorkommt
    while anfrag_idx > 0:

        # falls unmittelbar danach ":"
        temp_idx = text.find(":", anfrag_idx)
        temp_idx_2 = text.rfind(",", 0, anfrag_idx)

        if temp_idx - anfrag_idx < 20 and temp_idx > 0 and anfrag_idx - temp_idx_2 < 10:

            name_start_idx = find_word_start(text, temp_idx_2 - 2)

            # if name_start_idx > 0:
            name_end_idx = temp_idx_2

            assert (name_start_idx < name_end_idx)
            # if DEBUG: print("Schriftführer: ", name_start_idx, name_end_idx)

            anfrag = text[name_start_idx:name_end_idx]
            if DEBUG: print("Anfragender: ", anfrag)

            anfrags.append(anfrag)
            start_idc.append(name_start_idx)

        start = anfrag_idx + 1
        anfrag_idx = text.find("Anfragender", start)

    return anfrags, start_idc


def get_spec_speaker(text, type):

    # combine sekretär, anfragender, schriftführer

    DEBUG = False

    speakers = []
    start_idc = []

    # ######=== Find all type ===#######
    start = 0
    start_idx = text.find(type, start)

    if start_idx == -1:
        if DEBUG: print("Kein", type, "gefunden")

    # solange type vorkommt
    while start_idx > 0:

        # falls unmittelbar danach ":"
        temp_idx = text.find(":", start_idx)
        temp_idx_2 = text.rfind(",", 0, start_idx)

        if temp_idx - start_idx < 40 and temp_idx > 0 and start_idx - temp_idx_2 < 10:

            name_start_idx = find_word_start(text, temp_idx_2 - 2)

            # if name_start_idx > 0:
            name_end_idx = temp_idx_2

            assert (name_start_idx < name_end_idx)
            # if DEBUG: print("Schriftführer: ", name_start_idx, name_end_idx)

            speaker = text[name_start_idx:name_end_idx]
            if DEBUG: print(type, ": ", speaker)

            speakers.append(speaker)
            start_idc.append(name_start_idx)

        start = start_idx + 1
        start_idx = text.find(type, start)

    return speakers, start_idc
