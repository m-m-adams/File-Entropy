import os
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class EntropyDatasetBuilder (object):
    def __init__(self, window_size, matrix_size, inputdir):
        self.window_size = window_size
        self.matrix_size = matrix_size
        self.vector_size = matrix_size ** 2

        self.inputdir = inputdir

        self.outputdir = 'outputfiles-{}_byte_window-{}x{}'.format(window_size, matrix_size, matrix_size)
        self.windowedoutputdir = os.path.join(self.outputdir,'WindowedOutputs')
        self.windowed_image_outputdir = os.path.join(self.outputdir, 'WindowedImageOutputs')
        self.normoutputdir = os.path.join(self.outputdir,'NormalizedOutputs')
        self.normalized_image_outputdir = os.path.join(self.outputdir, 'NormalizedImageOutputs')

        self.featurefile = 'featurevectors-{}_byte_window-{}x{}'.format(window_size,matrix_size,matrix_size)

        self.make_dirs()

        self.feature_matrix = []
        self.classified_matrix = []

    def make_dirs(self):
        if not os.path.exists(self.outputdir):
            os.makedirs(self.outputdir)

        if not os.path.exists(self.normoutputdir):
            os.makedirs(self.normoutputdir)

        if not os.path.exists(self.normalized_image_outputdir):
            os.makedirs(self.normalized_image_outputdir)

        if not os.path.exists(self.windowedoutputdir):
            os.makedirs(self.windowedoutputdir)

        if not os.path.exists(self.windowed_image_outputdir):
            os.makedirs(self.windowed_image_outputdir)

        # make the multithreading manager
        # manager=mp.Manager()
    def build_entropy_maps_from_exes(self):
        InputDict = {}
        for filename in os.listdir(self.inputdir):
            print(filename)
            feature_vector_builder = FileEntropyVectorCalculator(self.window_size, self. matrix_size, os.path.join(self.inputdir, filename))

            windowed_entropy = feature_vector_builder.get_file_entropy()
            np.save(os.path.join(self.windowedoutputdir, filename+'.npy'), windowed_entropy)
            self.SaveWindowedEntropyPlot(windowed_entropy, os.path.join(self.windowed_image_outputdir, filename+'.png'))

            normalized_entropy = feature_vector_builder.normalize_entropy()
            np.save(os.path.join(self.normoutputdir, filename + '.npy'), normalized_entropy)
            self.SaveNormalizedEntropyPlot(normalized_entropy, os.path.join(self.normalized_image_outputdir, filename+'.png'))

            InputDict[filename] = np.reshape(normalized_entropy, (self.vector_size))

        InputMatrix = pd.DataFrame.from_dict(InputDict, orient='index')
        self.feature_matrix = InputMatrix
        self.GenerateLabels()
        return self.classified_matrix

    def GenerateLabels(self):
        ClassMatrix = self.feature_matrix.reset_index()
        ClassMatrix['class'] = ClassMatrix['index']
        ClassMatrix = ClassMatrix.set_index('index')
        for i, row in ClassMatrix.iterrows():
            label = row["class"]
            label = label[:-4]
            label = label.rstrip('1234567890.v')
            print(label)
            ClassMatrix.at[i, 'class'] = label
        new_columns = ['class'] + (ClassMatrix.columns.drop('class').tolist())
        ClassMatrix = ClassMatrix[new_columns]
        ClassMatrix.to_csv(os.path.join(self.outputdir, self.featurefile))
        self.classified_matrix = ClassMatrix
        return ClassMatrix

    @staticmethod
    def SaveNormalizedEntropyPlot(NormEnt, FileName):
        plt.ioff()
        plt.imshow(NormEnt, cmap='hot', interpolation='nearest')
        plt.axis('off')
        plt.savefig(FileName, bbox_inches='tight', transparent=True, pad_inches=0)

    @staticmethod
    def SaveWindowedEntropyPlot(EntList, FileName):
        # find the nearest square dimension
        dimension = int(math.ceil(math.sqrt(len(EntList))))
        # pad binary to make it a square number of windows
        EntList += [0] * (dimension ** 2 - len(EntList))
        array = np.array(EntList, dtype=np.uint8)
        array = np.reshape(EntList, (dimension, dimension))
        plt.ioff()
        plt.imshow(array, cmap='hot', interpolation='nearest')
        plt.axis('off')
        plt.savefig(FileName, bbox_inches='tight', transparent=True, pad_inches=0)

class FileEntropyVectorCalculator(object):

    def __init__(self,window_size, matrix_size, filename):
        self.window_size = window_size
        self.matrix_size = matrix_size
        self.filename = filename
        self.windowed_entropy = []
        self.normalized_entropy = []

    def get_file_entropy(self):
        # arbitrary, but reading in 32kb chunks is a good size for efficiency

        chunksize = 32768

        with open(self.filename, 'rb') as f:
            for chunk in iter(lambda: f.read(chunksize), b''):
                chunkwindows = self.get_windowed_entropy(chunk)
                for blockentropy in chunkwindows:
                    self.windowed_entropy.append(blockentropy)
        return self.windowed_entropy

    def get_windowed_entropy(self, barray):
        windowedEntropy = []
        for window in range(0, len(barray), self.window_size):
            wFreqs = self.CalcFreqs(barray[window:window + self.window_size - 1])
            wEnt = self.CalcEnt(wFreqs)
            windowedEntropy.append(2 ** wEnt)
        return windowedEntropy

    def normalize_entropy(self):
        NormPlot=np.zeros((self.matrix_size,self.matrix_size))
        divider=256//self.matrix_size
        last_entropy=0
        for entropy in self.windowed_entropy:
            current_entropy = int(entropy/divider)
            NormPlot[current_entropy,last_entropy]+=1
            last_entropy=current_entropy
        return NormPlot/len(self.windowed_entropy)

    @staticmethod
    def CalcFreqs(byteArr):
        freqList = []
        for b in range(256):
            ctr = 0
            for byte in byteArr:
                if byte == b:
                    ctr += 1
            freqList.append(float(ctr) / len(byteArr))
        return freqList

    @staticmethod
    # Shannon entropy based on input probability distribution
    def CalcEnt(freqlist):
        ent = 0.0
        for freq in freqlist:
            if freq > 0:
                ent = ent + freq * math.log(freq, 2)
        ent = -ent
        return ent

if __name__ == '__main__':
    window_size = 256
    matrix_size = 32
    inputdir = 'testfiles'
    entropy_image = EntropyDatasetBuilder(window_size, matrix_size, inputdir)
    feature_matrix = entropy_image.build_entropy_maps_from_exes()