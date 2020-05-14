from functions import *
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from bs4 import BeautifulSoup
from sklearn.model_selection import train_test_split
from gensim.models.doc2vec import TaggedDocument
import numpy as np
from tqdm import tqdm
tqdm.pandas(desc="progress-bar")
from gensim.models import Doc2Vec
from sklearn import utils, preprocessing
import gensim
from sklearn.linear_model import LogisticRegression
import multiprocessing
from sklearn.metrics import accuracy_score, f1_score
from gensim.test.test_doc2vec import ConcatenatedDoc2Vec


def sitzungen_list_von_bis(start, end):
    sitzungen = []
    ints = range(start, end+1)
    for number in ints:
        string = str(number)
        while len(string) < 3:
            string = "0" + string
        sitzungen.append(string)
    return sitzungen



def get_data(wahlperioden, sitzungen, verbose, save_files):

    tuples = []
    data = []
    fails = []
    successes = []

    for wahlperiode in wahlperioden:
        for sitzung in sitzungen:
            id = wahlperiode + sitzung

            path = "/Users/nektarioswinter/Documents/PoliticianProject/protokolle/pp" + id[:2] + "-data/" + id + ".xml"
            if not os.path.exists(path):
                print("\n", id, "not found")
                print("Skipping to the next one!")
                fails.append(id)
                continue

            print("\n==== Now working on " + str(id) + "! ====")

            reset_globals(verbose)

            temp_success_0_1, temp_fail_0_2 = extract_xml_txt(id, verbose, save_files)
            if not temp_success_0_1 or temp_fail_0_2: 
                print("Skipping to the next one!")
                fails.append(id)
                continue

            remove_brackets(id, verbose, save_files)
            get_speaker_names(id, verbose, save_files)
            connect_words(id, verbose, save_files)
            
            temp_fail_1 = get_page_idc(id, verbose, save_files)
            if temp_fail_1: 
                print("get_page_idc Error")
                print("Skipping to the next one!")
                fails.append(id)
                continue

            
            remove_header(id, verbose, save_files)
            
            temp_fail_2 = get_all_info(id, verbose, save_files)
            if temp_fail_2: 
                print("get_all_info Error")
                print("Skipping to the next one!")
                fails.append(id)
                continue
            
            temp_fail_3 = add_bundes_president(id, verbose, save_files)
            if temp_fail_3: 
                print("add_bundes_president Error")
                print("Skipping to the next one!")
                fails.append(id)
                continue

            # mark_idc_in_text(id, verbose, save_files, make_files_new)

            temp_fail_4 = add_speech_end_idx(id, verbose, save_files)  # why is the fail state order dependent
            if temp_fail_4: 
                print("add_speech_end_idx Error")
                print("Skipping to the next one!")
                fails.append(id)
                continue

            write_speeches_file(id, verbose, save_files)
            remove_cont_names(id, verbose, save_files)
            remove_line_break(id, verbose, save_files)
            trio_tuple = get_speaker_party_speech_tuples(id, verbose, save_files)
            print("A total amount of", len(trio_tuple), "Speeches were saved!")

            tuples.append(trio_tuple)
            successes.append(id)

            data.append((id, tuples))

    print("\n==== TOTAL DOCUMENTS:", str(len(wahlperioden)*len(sitzungen)), "====")
    print("====", len(successes), "Successes:", successes, "====")
    print("====", len(fails), "Fails:", fails, "====\n")

    return tuples