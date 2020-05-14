from get_data import *

def split_data(data):
    speakers = []
    parties = []
    speeches = []
    for i in range(len(data)):
        for j in range(len(data[i])):
            # print(data[i][j])
            speaker, party, speech = data[i][j]
            speakers.append(speaker)
            parties.append(party)
            speeches.append(speech)
    return speakers, parties, speeches


def print_info(df):
    # print(df)
    print("DataFrame Shape: ", df.shape)

    df.index = range(df.shape[0])
    print("Amount of words: ", df['Rede'].apply(lambda x: len(x.split(' '))).sum())
    print("\n")


def plot_parties(df):
    cnt_pro = df['Partei'].value_counts()
    plt.figure(figsize=(12,4))
    sns.barplot(cnt_pro.index, cnt_pro.values, alpha=0.8)
    plt.ylabel('Number of Occurrences', fontsize=12)
    plt.xlabel('Partei', fontsize=12)
    plt.xticks(rotation=90)
    plt.show();


def cleanText(text):
    text = BeautifulSoup(text, "lxml").text
    text = re.sub(r'\|\|\|', r' ', text) 
    text = re.sub(r'http\S+', r'<URL>', text)
    text = text.lower()
    text = text.replace('x', '')
    return text


def tokzr_SENT(txt): 
    return (re.findall(r'(?ms)\s*(.*?(?:\.|\?|!))', txt))


def tokenize_text(text):
    tokens = []
    sentences = tokzr_SENT(text)
    for sent in sentences:
        words = tokzr_SENT(sent)
        for word in words:
            if len(word) < 2:
                continue
            tokens.append(word.lower())
    return tokens


def vec_for_learning(model, tagged_docs):
    sents = tagged_docs.values
    targets, regressors = zip(*[(doc.tags[0], model.infer_vector(doc.words, steps=20)) for doc in sents])
    return targets, regressors


def get_vectors(model, tagged_docs):
    sents = tagged_docs.values
    targets, regressors = zip(*[(doc.tags[0], model.infer_vector(doc.words, steps=20)) for doc in sents])
    return targets, regressors