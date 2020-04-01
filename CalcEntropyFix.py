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


def BuildComparisons(inputdir,matrixsize):
    comparisonmatrix=pd.DataFrame(data=None,index=os.listdir(inputdir),columns=os.listdir(inputdir))
    vectorsize=matrixsize*matrixsize
    for file1 in os.listdir(inputdir):
        if file1.lower().endswith('.exe'):
            Array1=np.load(os.path.join('NormRawOutputs',file1+'.npy'))
            for file2 in os.listdir(inputdir):
                if file2.lower().endswith('.exe'):
                    Array2=np.load(os.path.join('NormRawOutputs',file2+'.npy'))
                    Similarity=(1-dist.cosine(np.reshape(Array1,(1,vectorsize)),np.reshape(Array2,(1,vectorsize))))**2
                    comparisonmatrix[file1][file2]=Similarity
                    if Similarity>0.5 and file1!=file2:
                        print(file1,file2,Similarity)
    return comparisonmatrix


if __name__=='__main__':

    window_size = 2048
    matrix_size = 16
    vector_size = matrix_size**2
    if not os.path.exists('WindowImageOutputs'):
        os.makedirs('WindowImageOutputs')

    if not os.path.exists('NormImageOutputs'):
        os.makedirs('NormImageOutputs')

    if not os.path.exists('NormRawOutputs'):
        os.makedirs('NormRawOutputs')

    inputdir='testfiles'

    InputDict = {}

    for filename in os.listdir(inputdir):
        print(filename)
        if not os.path.exists(os.path.join('NormRawOutputs',filename+'.npy')):
            byteArr=GetBytes(os.path.join(inputdir,filename))
            #freqList=CalcFreqs(byteArr)
            WinEnt = GetWindowedEntropy(byteArr,window_size)

            NormEnt = GetNormalizedEntropyPlot(WinEnt,matrix_size)
            np.save(os.path.join('NormRawOutputs',filename+'.npy'), NormEnt)
            print('finished')
            try:
                SaveWindowedEntropyPlot(WinEnt, os.path.join('WindowImageOutputs', filename + '.png'))
                SaveNormalizedEntropyPlot(NormEnt, os.path.join('NormImageOutputs', filename + '.png'))
            except:
                pass
            featurevector=np.reshape(NormEnt, (vector_size))
            print(featurevector)
            InputDict[filename]=featurevector
        else:
            NormEnt = np.load(os.path.join('NormRawOutputs', filename + '.npy'))
            featurevector = np.reshape(NormEnt, (vector_size))
            InputDict[filename] = featurevector

    InputMatrix = pd.DataFrame(InputDict)
    InputMatrix.to_csv('featurevectors.csv')

    df=ComparisonMatrix[ComparisonMatrix.columns].astype(float)

    sns.heatmap(df)
    plt.show()
    df.to_csv('output.csv')
