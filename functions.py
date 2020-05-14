from lower_funcs import *


def extract_xml_txt(id, verbose, save_files):
    # Takes XML File of a single session and formats it into a .txt file

    # if save_file --> if make_files_new --> xml_to_txt
    # if save_file --> if NOT make_files_new --> return true
    # if not save_file --> return true and save text

    # === PROBABLY APPLICABLE TO ALL YEARS ===
    if create_dirs(id, verbose, save_files):  # return True if successful
        if save_files:
            remove_all_files(id, verbose, minutes_path)
            success, text, fail = xml_to_txt(id, verbose, save_files)
        else:
            global xml_text
            success, xml_text, fail = xml_to_txt(id, verbose, save_files)

    return success, fail


def remove_brackets(id, verbose, save_files):
    # Removes all brackets that are not around party-names or part of listings (e.g. "a)")

    DEBUG = False
    global files_dir

    # === If file already exists, skip function, if not, create new one and continue ===
    files_dir = minutes_path + id[:2] + "/" + id + "/"

    if save_files:
        text = get_text_from_file("raw", id)
    else:
        global xml_text
        text = xml_text

    # === Repeat for every start bracket in text ===
    start = 0
    while text.find("(", start) > 0:
        if DEBUG: print("WHILE")

        strt_brkt = text.find("(", start)
        end_brkt = text.find(")", start)

        if end_brkt == -1:
            text = remove_text(text, strt_brkt-1, len(text), DEBUG)
            break

        # === e.g. "a)" überspringen ===
        if strt_brkt > end_brkt:
            start = end_brkt + 1  # start after the bracket
            continue

        # === If text between brackets is Party ===
        if text_is_party(text, strt_brkt, end_brkt):
            start = end_brkt + 1  # start after the bracket
            continue
        else:
            text = remove_text(text, strt_brkt, end_brkt, DEBUG)

    if save_files:
        txt_path = files_dir + id + "-nobrackets.txt"
        write_txt_file(txt_path, text, verbose)
    else:
        global no_brackets_text
        no_brackets_text = text


def connect_words(id, verbose, save_files):

    if save_files:
        text = get_text_from_file("nobrackets", id)
    else:
        global no_brackets_text
        text = no_brackets_text

    # === If file already exists, skip function, if not, create new one and continue ===
    files_dir = minutes_path + id[:2] + "/" + id + "/"

    i = 0
    strich_index = text.find("-\n", i)
    while strich_index > 0:
        if text[strich_index-1].islower():
           text = text[:strich_index] + text[strich_index+2:]
        i = strich_index + 1
        strich_index = text.find("-", i)

    if save_files:
        txt_path = files_dir + id + "-nobreaks.txt"
        write_txt_file(txt_path, text, verbose)
    else:
        global no_breaks_text
        no_breaks_text = text


def get_page_idc(id, verbose, save_files):

    # === Initialize parameters ===
    global speaker_names
    global page_start_idc
    global page_end_idc

    fail = False

    DEBUG_start = False
    DEBUG_end = False
    DEBUG = DEBUG_start or DEBUG_end

    page_start_idc = []
    page_start_idc.append(0)  # as the first page begins on 0
    if DEBUG: print("\nPage Start Index: 0\n")

    page_end_idc = []
    cnt = 0
    start_idx = 0

    if save_files:
        text = get_text_from_file("nobreaks", id)
    else:
        global no_breaks_text
        text = no_breaks_text

    bundestag_idx = text.find("Deutscher Bundestag", start_idx)

    # === Repeat for every occurence of "Deutscher Bundestag" which only appears in the header part ===
    # === as long as occurences are found (not found --> idx = -1 )===
    while bundestag_idx > 0:

        # === only if Deutscher Bundestag is followed by Wahlperiode will it count ===
        if text.find("Wahlperiode", bundestag_idx) - bundestag_idx < 30:

            # ##########=== Get Page End Index ===##########
            page_end_idx = add_page_end_idx(text, bundestag_idx, cnt)
            page_end_idc.append(page_end_idx)

            # ##########=== Figure out Page Start Index ===##########
            page_start_idx = add_page_start_idx(text, bundestag_idx, speaker_names, id)
            page_start_idc.append(page_start_idx)

        # ##########=== start looking for occurences starting from after the previous occurence ===##########
        start_idx = bundestag_idx + 1
        # if DEBUG: print("New start idx: " + str(start_idx))

        # === Next occurence of "Deutscher Bundestag" ===
        bundestag_idx = text.find("Deutscher Bundestag", start_idx)
        cnt += 1

        # if DEBUG: print("\n")

    page_end_idc.append(len(text))  # complete end of text is also a page end
    if DEBUG: print("Page End Index: " + str(len(text)) + "\n")

    fail = debugs_and_asserts(DEBUG, page_start_idc, page_end_idc, text)
    if verbose: print("Found start and end indices to all pages!")
    if DEBUG: print("\n")

    return fail


def remove_header(id, verbose, save_files):
    DEBUG = False

    global files_dir
    global page_start_idc
    global page_end_idc

    test_page = False

    # === Open and Read No Bracket File ===
    if save_files:
        text = get_text_from_file("nobreaks", id)
    else:
        global no_breaks_text
        text = no_breaks_text

    # === If test page, save only the first page in txt file, if not, save all pages ===
    pure_text = get_pure_text(DEBUG, page_start_idc, page_end_idc, text, test_page)

    if save_files:
        if test_page:
            write_txt_file(files_dir + id + "-testpage.txt", pure_text, verbose)
        else:
            write_txt_file(files_dir + id + "-noheader.txt", pure_text, verbose)
    else:
        global no_header_text
        no_header_text = pure_text

    # === there shouldnt be any more occurences of it ===
    occ_idx = pure_text.find("Deutscher Bundestag")
    if occ_idx != -1:
        if pure_text.find("Wahlperiode", occ_idx) != -1:
            assert(pure_text.find("Wahlperiode", occ_idx) - occ_idx > 40)


def get_speaker_names(id, verbose, save_files):
    global speaker_names

    DEBUG = False

    if save_files:
        text = get_text_from_file("nobrackets", id)  # worked with "noheader"
    else:
        global no_brackets_text
        text = no_brackets_text

    start = 0

    # === Do the following for all brackets left in document that are not "a)" ===
    while text.find("(", start) > 0:
        strt_brkt = text.find("(", start)
        end_brkt = text.find(")", start)

        # === skip the "a)" ===
        if strt_brkt > end_brkt:
            start = end_brkt + 1
            continue

        speaker_name, speaker_idx, party = get_speaker_and_party(text, strt_brkt)

        assert ("Dr." not in speaker_name)  # retarded .. Dr could be part of the name

        if is_faulty(speaker_name, DEBUG):
            continue

        speaker_names.append(speaker_name)

        start = end_brkt + 1  # go to next bracket)

    if verbose: print("Extracted speaker names!")


def get_all_info(id, verbose, save_files):
    # get list of all speeches (start of name of speaker)
    # start of name: after single letter, number, period (without preceding "Dr")
    # or exclamation mark, whichever comes first

    # as well as the indices of the speakers for later use

    #TODO: there are some speakers without (party) so filter them out by ":" and upperletter after
    # ... e.g. 18113 Tobias Lindner

    global speaker_party_speech_idc
    global speaker_names

    DEBUG = False
    fail = False

    if save_files:
        text = get_text_from_file("noheader", id)  # worked with "noheader"
    else:
        global no_header_text
        text = no_header_text

    start = 0

    # === Do the following for all brackets left in document that are not "a)" ===
    while text.find("(", start) > 0:
        strt_brkt = text.find("(", start)
        end_brkt = text.find(")", start)

        # === skip the "a)" ===
        if strt_brkt > end_brkt:
            start = end_brkt + 1
            continue

        # if DEBUG: print(text[strt_brkt - 40:strt_brkt + 3:])  # print(text[index-3:index+3:])
        # if DEBUG: print(text[end_brkt - 3:end_brkt + 3:])

        speaker_name, speaker_idx, party = get_speaker_and_party(text, strt_brkt)

        assert("Dr." not in speaker_name)  # retarded .. Dr could be part of the name

        if is_faulty(speaker_name, DEBUG):
            continue

        speech_strt_idx, fail = get_speech_strt_idx(text, end_brkt)

        if not fail:

            assert(type(speech_strt_idx) == int)

            speaker_party_speech_idc.append((speaker_idx, speaker_name, party, speech_strt_idx))

            if DEBUG: print("Added new tuple: ", (speaker_idx, speaker_name, party, speech_strt_idx))

        elif fail:
            # print("FAIL did not find speech start!")
            break

        start = end_brkt + 1  # go to next bracket)

    if verbose: print("Extracted speakers!")
    return fail

def add_bundes_president(id, verbose, save_files):

    # TODO: unify the method of getting secretaries/Schriftführer/anfragende .... exactly the same procedure

    DEBUG = False

    # TODO: add e.g. "Schriftführer"
    # TODO: split in lower functions
    # --> to not forget any speaker or to skip speakers --> have a complete list of all speech-starts to be sure

    global speaker_party_speech_idc
    global speaker_names

    if save_files:
        text = get_text_from_file("noheader", id)
    else:
        global no_header_text
        text = no_header_text

    bundes_speakers, bundes_speakers_start_idc = get_bundes_speakers(text)
    pres_speakers, pres_speakers_start_idc = get_pres_speakers(text)
    # secr_speakers, secr_speakers_start_idc = get_secr_speakers(text)
    # schrift_speakers, schrift_speakers_start_idc = get_schrift_speakers(text)
    # anfrag_speakers, anfrag_speakers_start_idc = get_anfragender_speakers(text)

    secr_speakers, secr_speakers_start_idc = get_spec_speaker(text, "Sekretär")
    schrift_speakers, schrift_speakers_start_idc = get_spec_speaker(text, "Schriftführer")
    anfrag_speakers, anfrag_speakers_start_idc = get_spec_speaker(text, "Anfragende")


    if not len(bundes_speakers_start_idc) == len(bundes_speakers) or not len(pres_speakers_start_idc) == len(pres_speakers) or not len(secr_speakers_start_idc) == len(secr_speakers) or not len(schrift_speakers_start_idc) == len(schrift_speakers):
        if verbose: print("Bundes/Präs/Sekr/Schrift Recognition FAIL 1!")
        return True

    # idx == current bundes/pres idx
    # speaker_idx == current speaker idx looked at from the total list
    for i in range(len(bundes_speakers_start_idc)):
        speaker_idx = bundes_speakers_start_idc[i]
        speech_strt_idx = get_bundes_pres_speech_strt(text, speaker_idx)

        assert(type(speech_strt_idx) == int)

        # speaker_idc.append(speaker_idx)
        # speaker_speech_strt.append(speech_strt_idx)

        speaker_names.append(bundes_speakers[i])
        speaker_idc = get_part_of_tuples(speaker_party_speech_idc, 1)
        if speaker_idx not in speaker_idc:
            speaker_party_speech_idc.append((speaker_idx, bundes_speakers[i], "Minister/in", speech_strt_idx))


    for i in range(len(pres_speakers_start_idc)):
        speaker_idx = pres_speakers_start_idc[i]
        speech_strt_idx = get_bundes_pres_speech_strt(text, speaker_idx)

        assert (type(speech_strt_idx) == int)

        # speaker_idc.append(speaker_idx)
        # speaker_speech_strt.append(speech_strt_idx)

        # I know I should fight the root of the problem (a speaker having the same index as a president ..
        # which shouldnt happen --> detection is wrong but this works just as well
        speaker_names.append(pres_speakers[i])
        speaker_idc = get_part_of_tuples(speaker_party_speech_idc, 1)
        if speaker_idx not in speaker_idc:
            speaker_party_speech_idc.append((speaker_idx, pres_speakers[i], "Präsident/in", speech_strt_idx))
        else:
            continue

    for i in range(len(secr_speakers_start_idc)):
        speaker_idx = secr_speakers_start_idc[i]
        speech_strt_idx = get_bundes_pres_speech_strt(text, speaker_idx)

        assert(type(speech_strt_idx) == int)

        speaker_names.append(secr_speakers[i])
        speaker_idc = get_part_of_tuples(speaker_party_speech_idc, 1)
        if speaker_idx not in speaker_idc:
            speaker_party_speech_idc.append((speaker_idx, secr_speakers[i], "Sekretär/in", speech_strt_idx))


    for i in range(len(schrift_speakers_start_idc)):
        speaker_idx = schrift_speakers_start_idc[i]
        speech_strt_idx = get_bundes_pres_speech_strt(text, speaker_idx)

        assert(type(speech_strt_idx) == int)

        speaker_names.append(schrift_speakers[i])
        speaker_idc = get_part_of_tuples(speaker_party_speech_idc, 1)
        if speaker_idx not in speaker_idc:
            speaker_party_speech_idc.append((speaker_idx, schrift_speakers[i], "Schriftführer/in", speech_strt_idx))


    for i in range(len(anfrag_speakers_start_idc)):
        speaker_idx = anfrag_speakers_start_idc[i]
        speech_strt_idx = get_bundes_pres_speech_strt(text, speaker_idx)

        assert(type(speech_strt_idx) == int)

        speaker_names.append(anfrag_speakers[i])
        speaker_idc = get_part_of_tuples(speaker_party_speech_idc, 1)
        if speaker_idx not in speaker_idc:
            speaker_party_speech_idc.append((speaker_idx, anfrag_speakers[i], "Anfragende/r", speech_strt_idx))


    # === sort the tuples by ascending speaker_start_idx order ===
    speaker_party_speech_idc.sort()
    for i in range(len(speaker_party_speech_idc) - 1):
        speaker_idx, speaker_name, party, speech_strt_idx = speaker_party_speech_idc[i]
        new_speaker_idx, new_speaker_name, new_party, new_speech_strt_idx = speaker_party_speech_idc[i + 1]

        # assert (speaker_idx < new_speaker_idx)
        if not speaker_idx < new_speaker_idx:
            if verbose: print("Bundes/Präs/Sekr Recognition FAIL 2!")
            return True

        if DEBUG: print("\n" + str(speech_strt_idx) + " " + text[speech_strt_idx-20:speech_strt_idx+20] + "\n")
        if DEBUG: print(speech_strt_idx)
        assert(type(speech_strt_idx) == int)

    if verbose: print("Added ministers and presidents to speakers!")

    return False


def mark_idc_in_text(id, verbose, save_files):
    global speaker_party_speech_idc

    DEBUG = False

    new_text = ""

    if save_files:
        text = get_text_from_file("noheader", id)
    else:
        global no_header_text
        text = no_header_text

    speaker_mark = " ############## SPEAKER: "
    speech_mark = " ############## SPEECH: "

    text_start_speaker = 0

    for i in range(len(speaker_party_speech_idc)):
        speaker_idx, speaker_name, party, speech_strt_idx = speaker_party_speech_idc[i]

        new_speaker_idx = speaker_idx
        new_speech_idx = speech_strt_idx

        new_text += text[text_start_speaker:new_speaker_idx] + speaker_mark
        new_text += text[new_speaker_idx:new_speech_idx] + speech_mark

        text_start_speaker = new_speech_idx

    if save_files:
        write_txt_file(files_dir + id + "-marked.txt", new_text, verbose)
    else:
        global mark_idc_text
        mark_idc_text = new_text


def remove_line_break(id, verbose, save_files):
    DEBUG = False

    if save_files:
        text = get_text_from_file("no_cont_names", id)
    else:
        global no_cont_names_text
        text = no_cont_names_text

    # === If file already exists, skip function, if not, create new one and continue ===
    files_dir = minutes_path + id[:2] + "/" + id + "/"

    new_text = ""
    start = 0

    break_idx = text.find("\n", start)

    if DEBUG: print(break_idx)

    while break_idx >= 0:

        if DEBUG: print(start, break_idx, text[start:break_idx])
        new_text += text[start:break_idx] + " "

        start = break_idx + 1

        break_idx = text.find("\n", start)

    txt_path = files_dir + id + "-nolinebreaks.txt"

    if save_files:
        write_txt_file(txt_path, new_text, verbose)
    else:
        global no_line_break_text
        no_line_break_text = new_text


def add_speech_end_idx(id, verbose, save_files):
    global speaker_party_speech_idc
    global full_list_idc

    DEBUG = False

    if save_files:
        text = get_text_from_file("noheader", id)
    else:
        global no_header_text
        text = no_header_text

    fail, speech_end_idc = get_speech_end_idc(text, speaker_party_speech_idc, verbose)

    if not fail:

        if not (len(speech_end_idc) == len(speaker_party_speech_idc)):
            fail = True
            return fail
        
        # assert(len(speech_end_idc) == len(speaker_party_speech_idc))

        for i in range(len(speech_end_idc)):
            speaker_idx, speaker_name, party, speech_strt_idx = speaker_party_speech_idc[i]
            speech_end_idx = speech_end_idc[i]

            full_list_idc.append((speaker_idx, speaker_name, party, speech_strt_idx, speech_end_idx))

            if DEBUG: print("Added new tuple: ", (speaker_idx, speaker_name, party, speech_strt_idx, speech_end_idx))

        if verbose: print("Found speech end indices!")

    return fail


def write_speeches_file(id, verbose, save_files):
    global full_list_idc
    global speaker_names
    global files_dir

    DEBUG = False

    speeches = ""

    if save_files:
        text = get_text_from_file("noheader", id)
    else:
        global no_header_text
        text = no_header_text

    for i in range(len(full_list_idc)):
        speaker_idx, speaker_name, party, speech_start_idx, speech_end_idx = full_list_idc[i]
        if DEBUG: print(speaker_name, speech_start_idx, speech_end_idx)
        speeches += "\n############## START SPEECH ##################\n" + "SPEAKER: " + speaker_name + \
                    "\nPARTY: " + party + "\n##############################################\n"\
                    + text[speech_start_idx:speech_end_idx] + "\n################# END SPEECH #################\n"

    if save_files:
        write_txt_file(files_dir + id + "-speeches.txt", speeches, verbose)
    else:
        global speeches_text
        speeches_text = speeches


def remove_cont_names(id, verbose, save_files):
    DEBUG = False

    global speaker_names
    new_text = ""
    old_start = 0

    # === remove names of speakers of interrupted speeches that appear again in the middle (pre and succeeded by \n) ===
    if save_files:
        text = get_text_from_file("speeches", id)
    else:
        global speeches_text
        text = speeches_text

    if DEBUG: print("Gerstenmaier" in speaker_names)
    speaker_idc = get_speaker_continued_speech(speaker_names, text)

    for idc in speaker_idc:
        before_idx, after_idx = idc
        new_text += text[old_start:before_idx]

        old_start = after_idx

    new_text += text[old_start:len(text)]

    if save_files:
        write_txt_file(files_dir + id + "-no_cont_names.txt", new_text, verbose)
    else:
        global no_cont_names_text
        no_cont_names_text = new_text


def get_speaker_party_speech_tuples(id, verbose, save_files):
    trio_tuple = []

    DEBUG = False

    if save_files:
        text = get_text_from_file("nolinebreaks", id)
    else:
        global no_line_break_text
        text = no_line_break_text

    start = 0
    start_idx = text.find("############## START SPEECH ##################", start)

    while start_idx >= 0:
        speaker_start = text.find("SPEAKER: ", start_idx) + len("SPEAKER: ")
        speaker_end = text.find(" PARTY: ", speaker_start)
        speaker = text[speaker_start:speaker_end]

        party_start = text.find("PARTY: ", start_idx) + len("PARTY: ")
        party_end = text.find(" ##############################################", party_start)
        party = text[party_start:party_end]

        speech_start = text.find(" ##############################################", start_idx) + \
                       len(" ##############################################")
        speech_end = text.find(" ################# END SPEECH #################", start_idx)
        speech = text[speech_start:speech_end]

        # if DEBUG: print(" == Speaker: ", speaker, " == Party: ", party, " == Speech Length: ", str(len(speech)) + " == ")
        if party != "Präsident/in" and party != "Minister/in" and party != "Sekretär/in" and party != "Schriftführer/in" and party != "Anfragende/r":
            if DEBUG: print(" == Speaker: ", speaker, " == Party: ", party, " == Speech Length: ", str(len(speech)) + " == ")
            trio_tuple.append([speaker, party, speech])

        start_idx = text.find("############## START SPEECH ##################", start_idx) + 1

        if start_idx == 0:
            break

    if verbose: print("Saved every speaker, party and speech in array")

    # print(trio_tuple)
    return trio_tuple


def reset_globals(verbose):

    global xml_text
    global no_brackets_text
    global no_breaks_text
    global no_header_text
    global mark_idc_text
    global no_line_break_text
    global speeches_text
    global no_cont_names_text

    global page_start_idc
    global page_end_idc

    # === tuple of speaker start idx, party name (None for bundes/pres) and speech strt idx
    # (speaker name can be figured out very easily by idx) ===
    global speaker_party_speech_idc

    # === tuple of speaker start idx, speaker_name, party name (None for bundes/pres), speech strt idx and speech end idx ===
    global full_list_idc

    global speaker_names

    xml_text = ""
    no_brackets_text = ""
    no_breaks_text = ""
    no_header_text = ""
    mark_idc_text = ""
    no_line_break_text = ""
    speeches_text = ""
    no_cont_names_text = ""

    page_start_idc = []
    page_end_idc = []

    speaker_party_speech_idc = []

    full_list_idc = []

    speaker_names = []

    if verbose: print("All global variables reset!")