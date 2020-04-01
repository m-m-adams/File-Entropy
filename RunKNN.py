import os
import math
import scipy.spatial.distance as dist
import pandas as pd
import random
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neighbors import DistanceMetric

def CosineSquareDistance(vec1, vec2):
    return dist.cosine(vec1, vec2) ** 2


if __name__ == '__main__':
    input_file='labelledmalwarevectorstrimmed.csv'
    exe_vectors=pd.read_csv(input_file)
    feature_columns=exe_vectors.columns.drop(['class', 'index'])
    label_column = 'class'
    ntrials=200
    #print(feature_columns.values)
    #print(label_column)
    CumAccuracy=[]
    for trial in range(ntrials):
        random_indices = np.random.permutation(exe_vectors.index)
        test_cutoff = math.floor(len(exe_vectors)/10)
        test = exe_vectors.loc[random_indices[1:test_cutoff]]
        train = exe_vectors.loc[random_indices[test_cutoff:]]

        #dt = DistanceMetric.get_metric('pyfunc', func=CosineSquareDistance)


        #nbrs=KNeighborsClassifier(n_neighbors=2, metric='pyfunc', metric_params={'func':CosineSquareDistance})
        nbrs = KNeighborsClassifier(n_neighbors=2, metric='jaccard')
        nbrs.fit(train[feature_columns], train[label_column])

        predictions = nbrs.predict(test[feature_columns])
        actual = test[label_column]
        actual = actual.tolist()

        correct=0
        for n in range(len(test)):
            print('prediction was', predictions[n], 'actual was', actual[n])
            if predictions[n] == actual[n]: correct+=1
        accuracy = correct/len(test)
        CumAccuracy.append(accuracy)
        print('accuracy was:',accuracy)
    print('Cumulative accuracy was :', sum(CumAccuracy)/ntrials)