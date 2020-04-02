# file_entropy.py
#
# Shannon Entropy of a file
# = minimum average number of bits per character
# required for encoding (compressing) the file
#
# So the theoretical limit (in bytes) for data compression:
# Shannon Entropy of the file * file size (in bytes) / 8
# (Assuming the file is a string of byte-size (UTF-8?) characters
# because if not then the Shannon Entropy value would be different.)
# FB - 201011291
import sys
import os
import math
import scipy.spatial.distance as dist
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

# calculate the frequency of each byte value
def CalcFreqs(byteArr):
    freqList = []
    for b in range(256):
        ctr = 0
        for byte in byteArr:
            if byte == b:
                ctr += 1
        freqList.append(float(ctr) / len(byteArr))
    return freqList


# Shannon entropy based on input probability distribution
def CalcEnt(freqlist):
    ent = 0.0
    for freq in freqlist:
        if freq > 0:
            ent = ent + freq * math.log(freq, 2)
    ent = -ent
    return ent

# read the whole file into a byte array
def GetBytes(filename):
    f = open(filename, "rb")
    byteArr = bytearray(f.read())
    f.close()
    return byteArr

def GetWindowedEntropy(barray,WSize):
    windowedEntropy=[]
    for window in range(0, len(barray), WSize):
        wFreqs=CalcFreqs(barray[window:window+WSize-1])
        wEnt=CalcEnt(wFreqs)
        windowedEntropy.append(2**wEnt)
    return windowedEntropy


def GetNormalizedEntropyPlot(WindowedEntropy,matrixsize):
    NormPlot=np.zeros((matrixsize,matrixsize))
    divider=256//matrixsize
    last_entropy=0
    current_entropy=0
    for entropy in WindowedEntropy:
        current_entropy = int(entropy/divider)
        NormPlot[current_entropy,last_entropy]+=1
        last_entropy=current_entropy

    return NormPlot/len(WindowedEntropy)


def SaveNormalizedEntropyPlot(NormEnt,FileName):
    plt.imshow(NormEnt,cmap='hot',interpolation='nearest')
    plt.axis('off')
    plt.savefig(FileName,bbox_inches='tight',transparent=True, pad_inches=0)


def SaveWindowedEntropyPlot(EntList,FileName):
    #find the nearest square dimension
    dimension=int(math.ceil(math.sqrt(len(EntList))))
    #pad binary to make it a square number of windows
    EntList += [0] * (dimension**2 - len(EntList))
    array = np.array(EntList, dtype=np.uint8)
    array=np.reshape(EntList,(dimension,dimension))
    plt.imshow(array,cmap='hot',interpolation='nearest')
    plt.axis('off')
    plt.savefig(FileName,bbox_inches='tight', transparent=True, pad_inches=0)


def BuildComparisons(directory,matrixsize):
    comparisonmatrix=pd.DataFrame(data=None,index=os.listdir(directory),columns=os.listdir(directory))
    vectorsize=matrixsize*matrixsize
    for file1 in os.listdir(directory):
        Array1=np.load(os.path.join(directory,file1))
        for file2 in os.listdir(directory):
            Array2=np.load(os.path.join(directory,file2))
            Similarity=(1-dist.jaccard(np.reshape(Array1,(1,vectorsize)),np.reshape(Array2,(1,vectorsize))))
            comparisonmatrix.at[file1,file2]=Similarity
            #if Similarity>0.2:
                #print(file1,file2,Similarity)
    return comparisonmatrix

def BuildEntropyMapsRawExe(inputdir, windowedimageoutputdir, windowedoutputdir, normoutputdir, normimageoutputdir):
    if not os.path.exists(windowedimageoutputdir):
        os.makedirs(windowedimageoutputdir)

    if not os.path.exists(normimageoutputdir):
        os.makedirs(normimageoutputdir)

    if not os.path.exists(normoutputdir):
        os.makedirs(normoutputdir)

    InputDict = {}

    for filename in os.listdir(inputdir):
        print(filename)
        if not os.path.exists(os.path.join(normoutputdir,filename+'.npy')):
            byteArr=GetBytes(os.path.join(inputdir,filename))
            #freqList=CalcFreqs(byteArr)

            WinEnt = GetWindowedEntropy(byteArr,window_size)
            np.save(os.path.join(windowedoutputdir, filename + '.npy'), WinEnt)

            NormEnt = GetNormalizedEntropyPlot(WinEnt,matrix_size)
            np.save(os.path.join(normoutputdir,filename+'.npy'), NormEnt)
            print('finished')
            try:
                SaveWindowedEntropyPlot(WinEnt, os.path.join(windowedimageoutputdir, filename + '.png'))
                SaveNormalizedEntropyPlot(NormEnt, os.path.join(normimageoutputdir, filename + '.png'))
            except:
                pass
            featurevector=np.reshape(NormEnt, (vector_size))
            InputDict[filename]=featurevector


    InputMatrix = pd.DataFrame.from_dict(InputDict, orient='index')
    InputMatrix.to_csv('featurevectors-16x16.csv')

    ClassMatrix = InputMatrix.reset_index()
    ClassMatrix['class'] = ClassMatrix['index']
    ClassMatrix = ClassMatrix.set_index('index')
    for i, row in ClassMatrix.iterrows():
        label = row["class"]
        label = label[:-4]
        label = label.rstrip('1234567890.v')
        print(label)
        ClassMatrix.at[i, 'class'] = label
    new_columns = ['class']+(ClassMatrix.columns.drop('class').tolist())
    ClassMatrix = ClassMatrix[new_columns]
    ClassMatrix.to_csv('labelledfeaturevectors.csv')

    return ClassMatrix

def MatrixFromData(windowedentdir,outputfile):
    InputDict = {}
    for filename in os.listdir(windowedentdir):
        NormEnt = np.load(os.path.join(windowedentdir, filename))
        im = Image.fromarray(NormEnt)
        im=im.resize((matrix_size, matrix_size),Image.BILINEAR)
        NormEnt = np.asarray(im)

        featurevector = np.reshape(NormEnt, (vector_size))
        # print(featurevector)

        InputDict[filename] = featurevector
    InputMatrix = pd.DataFrame.from_dict(InputDict, orient='index')

    ClassMatrix = InputMatrix.reset_index()
    ClassMatrix['class'] = ClassMatrix['index']
    ClassMatrix = ClassMatrix.set_index('index')
    for i, row in ClassMatrix.iterrows():
        label = row["class"]
        label = label[:-4]
        label = label.rstrip('1234567890.v')
        print(label)
        ClassMatrix.at[i, 'class'] = label
    new_columns = ['class']+(ClassMatrix.columns.drop('class').tolist())
    ClassMatrix = ClassMatrix[new_columns]
    ClassMatrix.to_csv(outputfile)

    return ClassMatrix

if __name__=='__main__':

    window_size = 2048
    matrix_size = 32
    vector_size = matrix_size**2
    inputdir = 'testfiles'
    rawimageoutputdir='WindowImageOutputs'
    rawoutputdir='WindowOutputs'
    windowedoutputdir='NormRawOutputs - 256x256'
    windowedimageoutputdir='NormImageOutputs'
    outputfile='featurevectors-32x32.csv'

    #ClassifiedMatrix=BuildEntropyMapsRawExe(inputdir, rawimageoutputdir, rawoutputdir, windowedoutputdir, windowedimageoutputdir)
    ClassifiedMatrix=MatrixFromData(windowedoutputdir,outputfile)


    #ComparisonMatrix = BuildComparisons('NormRawOutputs', matrix_size)
    #df = ComparisonMatrix[ComparisonMatrix.columns].astype(float)

    #svm = sns.heatmap(df)
    #plt.show()
    #df.to_csv('output.csv')
    #figure = svm.get_figure()
    #figure.savefig('comparisons.png')

