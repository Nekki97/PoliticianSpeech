from get_data import *
from magic_functions import *

path = '/Users/nektarioswinter/Documents/PoliticianProject/protokolle/'
new_data = False

wahlperioden = ["01", "02", "03", "06", "10"] # , "06", "10", "15", "17", "18"
start_sitz = 1
end_sitz = 300

epochs = 30

data_path = path + "#" + str(len(wahlperioden)) + "_periods_" + str(start_sitz) + "-" + str(end_sitz) + "_sitz_data.csv"

if new_data:
	sitzungen = sitzungen_list_von_bis(start_sitz, end_sitz)

	# sitzungen = ["001", "002", "003", "004", "010", "011", "012"]

	verbose = False        # get feedback on current operation
	save_files = False      # save text in files for every stage of processing


	# array of triples: (speaker, party, speech) of all speakers (no präsident, minister, sekretär)
	data = get_data(wahlperioden, sitzungen, verbose, save_files)
	speakers, parties, speeches = split_data(data)

	# change data type to pandas DataFrame with only parties and speeches .. no speaker names for now
	df = pd.DataFrame(list(zip(parties, speeches)), columns=["Partei", "Rede"])

	df.to_csv(data_path, index = False)

if not new_data:
	df = pd.read_csv(data_path)

# print(df['Rede'])
# print(df['Rede'].values)

print_info(df)
# plot_parties(df)

df['Rede'] = df['Rede'].apply(cleanText)

print("Split into Train and Test!")
train, test = train_test_split(df, test_size=0.3, random_state=42)

# print(df[0].shape(), df[1].shape())

train_tagged = train.apply(lambda r: TaggedDocument(words=tokenize_text([x for x in df["Rede"].values()]), tags=[x for x in df["Partei"].values()]), axis=1)
test_tagged = test.apply(lambda r: TaggedDocument(words=tokenize_text([x for x in df["Rede"].values()]), tags=[x for x in df["Partei"].values()]), axis=1)

print(train_tagged, test_tagged)

# ###=== TODO: look at details of speeches, how many words, distribution of word count etc ===####

cores = multiprocessing.cpu_count()

print("Create Doc2Vec model!")
model_dbow = Doc2Vec(dm=0, vector_size=300, negative=5, hs=0, min_count=10, sample = 0, workers=cores)
model_dbow.build_vocab([x for x in tqdm(train_tagged.values)])

model_dbow.wv.vocab

model_dmm = Doc2Vec(dm=1, dm_mean=1, vector_size=300, window=10, negative=5, min_count=1, workers=5, alpha=0.065, min_alpha=0.065)
model_dmm.build_vocab([x for x in tqdm(train_tagged.values)])

new_model = ConcatenatedDoc2Vec([model_dbow, model_dmm])

print("Train first model!")
for epoch in range(epochs):
    model_dbow.train(utils.shuffle([x for x in tqdm(train_tagged.values)]), total_examples=len(train_tagged.values), epochs=1)
    model_dbow.alpha -= 0.002
    model_dbow.min_alpha = model_dbow.alpha

print("Train second model!")
for epoch in range(epochs):
	model_dmm.train(utils.shuffle([x for x in tqdm(train_tagged.values)]), total_examples=len(train_tagged.values), epochs=1)
	model_dmm.alpha -= 0.002
	model_dmm.min_alpha = model_dmm.alpha

# X_train = preprocessing.scale(X_train)

'''
y_train, X_train = vec_for_learning(model_dbow, train_tagged)
y_test, X_test = vec_for_learning(model_dbow, test_tagged)
logreg = LogisticRegression(n_jobs=5, C=1e5, max_iter=2000, verbose=1)
logreg.fit(X_train, y_train)
y_pred = logreg.predict(X_test)
'''

# ####=== TODO: look at data exactly ... what form xtrain xtest ytrain and ytest have in vector form to understand it better ==== 

print("Create vectors of speeches!")
y_train, X_train = get_vectors(new_model, train_tagged)
y_test, X_test = get_vectors(new_model, test_tagged)

print("1:", len(y_train), "2:", len(X_train), "3:", len(y_test), "4:", len(X_test))

print("Save sets in txt file!")
write_txt_file(path + "y_train.txt", str(y_train[0]), 1)
write_txt_file(path + "X_train.txt", str(X_train[0]), 1)
write_txt_file(path + "y_test.txt", str(y_test[0]), 1)
write_txt_file(path + "X_test.txt", str(X_test[0]), 1)

X_train = preprocessing.scale(X_train)

write_txt_file(path + "X_train_scaled.txt", str(X_train[0]), 1)

print("Starting Logistic Regression!")
logreg = LogisticRegression(n_jobs=-1, C=1e5, max_iter=2000, verbose=1)
logreg.fit(X_train, y_train)
y_pred = logreg.predict(X_test)

print("\n=======================")
print('Testing accuracy %s' % round(accuracy_score(y_test, y_pred), 3))
print('Testing F1 score: {}'.format(round(f1_score(y_test, y_pred, average='weighted'), 3)))
print("=======================\n")
