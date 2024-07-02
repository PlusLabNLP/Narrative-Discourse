
import csv

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import matplotlib.pyplot as plt
stop_words = set(stopwords.words('english'))
def remove_stop_words(text):
    word_tokens = word_tokenize(text)
    filtered_text = [w for w in word_tokens if not w.lower() in stop_words]
    filtered_text = [i for i in filtered_text if i != "like"]
    return filtered_text

def get_NRC_lexicon(path):
    '''
    @output:
    - A dictionary of format {word : score}
    '''
    lexicon = path
    val_dict = {}
    aro_dict = {}
    dom_dict = {}
    with open(lexicon, 'r') as infile:
        reader = csv.DictReader(infile, delimiter="\t")
        for row in reader:
            word = row['Word']
            val_dict[word] = float(row['Valence'])
            aro_dict[word] = float(row['Arousal'])
            dom_dict[word] = float(row['Dominance'])
    return (val_dict, aro_dict, dom_dict)


val_dict, aro_dict, _ = get_NRC_lexicon("/Users/huangtenghao/git/story_analysis/NRC-VAD-Lexicon.txt")

def get_arousal_score(infs):
    '''
    input:
        infs: a list of commonsense inferences
    output:
        score: the sum of valence valence scores
    '''
    if infs ==[]:
        return None,None
    sum = 0
    # print(infs)
    rt_l = []
    total_cnt = 0
    for inf in infs:
        inf = remove_stop_words(inf)

        sub_scores = []
        cnt = 0
        for part in inf:
            if part not in aro_dict:
                continue
            cnt+=1
            sub_scores.append(aro_dict[part])
        total_cnt += cnt
        if sub_scores == []:
            continue
        sum+= max(sub_scores)
        rt_l.append(max(sub_scores))
    return sum, rt_l, total_cnt

def get_corpus_valence_score(corpus):
    corpus = corpus.split(" ")
    words = [i.strip(".") for i in corpus]
    rt = []
    for word in words:
        score = val_dict.get(word,-1)
        if score != -1:
            rt.append(score)
    return sum(rt)/len(rt) if len(rt)!=0 else -1

def get_valence_score(infs):
    '''
    input:
        infs: a list of commonsense inferences
    output:
        score: the sum of valence valence scores
    '''
    if infs ==[]:
        return None,None
    sum = 0

    rt_l = []
    for inf in infs:
        inf = remove_stop_words(inf)

        sub_scores = []
        cnt = 0
        for part in inf:
            if part not in val_dict:
                continue
            cnt+=1
            sub_scores.append(val_dict[part])
        if sub_scores == []:
            continue
        sum+= max(sub_scores)
        rt_l.append(max(sub_scores))
    return sum,rt_l


import numpy as np


def plot_fitting_curve(scores, polynomial, plotting=True, color=None):
    x = positions = list(range(len(scores)))
    # x = [score[0] for score in scores]
    y = scores

    # calculate polynomial
    z = np.polyfit(x, y, polynomial)
    f = np.poly1d(z)

    # calculate new x's and y's
    x_new = np.linspace(x[0], x[-1], 50)
    y_new = f(x_new)

    #     print(len(y_new))
    if plotting:
        plt.plot(x, y, 'o', x_new, y_new, color=color)
        plt.xlim([x[0] - 1, x[-1] + 1])
    return y_new


def get_interpolated_overall_scores(inferences, polynomial=15):
    if inferences == []:
        return None, None
    ensemble = []
    for _ in range(len(inferences)):
        try:
            splited = [i.split(", ") for i in inferences[_]['st_emo']]
        except:
            print(_)
            continue
        aoursal_overall = []
        valence_overall = []
        for l in splited:
            if len(l) != 3:
                print(l)
                continue
            tmps = []
            for i in l:
                i = i.lower()
                i = i.strip(".[] ")
                i.replace('and ', '')
                tmps.append(i)
            # take the top 1 sentiment
            tmps = tmps[:2]
            a_score, a_rt_l, _ = get_arousal_score(tmps)
            v_score, v_rt_l = get_valence_score(tmps)
            if len(a_rt_l) != 0:
                aoursal_overall.append(a_score / len(a_rt_l))
            else:
                last_item = aoursal_overall[-1]
                aoursal_overall.append(last_item)
            if len(v_rt_l) != 0:
                valence_overall.append(v_score / len(v_rt_l))
            else:
                last_item = valence_overall[-1]
                valence_overall.append(last_item)

        ensemble.append([plot_fitting_curve(aoursal_overall, polynomial=polynomial, plotting=False), \
                         plot_fitting_curve(valence_overall, polynomial=polynomial, plotting=False)])
    average = np.mean(ensemble, axis=0)
    return average, ensemble

