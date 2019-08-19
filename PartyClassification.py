from functions import *

wahlperiode = "14"
sitzung = "010"
id = wahlperiode + sitzung

load_protocol(wahlperiode, sitzung, 1)
crop_merge_pdf(id, 1)
convert_pdf_to_txt(id, 1)
remove_brackets(id, 1)
indices = get_speech_indices(id, 1)