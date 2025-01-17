import os
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class EntropyDatasetBuilder (object):
    def __init__(self, window_size, matrix_size, inputdir, datasetdir):
        self.window_size = window_size
        self.matrix_size = matrix_size
        self.vector_size = matrix_size ** 2

        self.inputdir = inputdir

        self.outputdir = os.path.join('output', 'outputfiles-{}_byte_window-{}x{}'.format(window_size, matrix_size, matrix_size))

        self.featurefile = os.path.join(datasetdir, 'featurevectors-{}_byte_window-{}x{}.csv'.format(window_size,matrix_size,matrix_size))

        self.make_dirs()

        self.feature_matrix = []
        self.classified_matrix = []

    def make_dirs(self):
        if not os.path.exists(self.outputdir):
            os.makedirs(self.outputdir)

        # make the multithreading manager
        # manager=mp.Manager()
    def build_entropy_maps_from_exes(self):
        InputDict = {}
        for filename in os.listdir(self.inputdir):
            print(filename)
            feature_vector_builder = FileEntropyVectorCalculator(self.window_size, self. matrix_size, filename, self.inputdir, self.outputdir)

            feature_vector_builder.get_file_entropy()
            normalized_entropy = feature_vector_builder.normalize_entropy()
            feature_vector_builder.save_arrays()
            feature_vector_builder.save_images()


            InputDict[filename] = np.reshape(normalized_entropy, (self.vector_size))

        InputMatrix = pd.DataFrame.from_dict(InputDict, orient='index')
        np.save(os.path.join(self.outputdir, 'unclassifiedvectors'), InputMatrix)
        self.feature_matrix = InputMatrix
        self.GenerateLabels()
        self.classified_matrix.to_csv(self.featurefile)
        return self.classified_matrix

    def GenerateLabels(self):
        ClassMatrix = self.feature_matrix.reset_index()
        ClassMatrix['class'] = ClassMatrix['index']
        ClassMatrix = ClassMatrix.set_index('index')
        for i, row in ClassMatrix.iterrows():
            label = row["class"]
            label = label[:-4]
            label = label.rstrip('1234567890.v')
            ClassMatrix.at[i, 'class'] = label
        new_columns = ['class'] + (ClassMatrix.columns.drop('class').tolist())
        ClassMatrix = ClassMatrix[new_columns]
        self.classified_matrix = ClassMatrix
        return ClassMatrix

class FileEntropyVectorCalculator(object):

    def __init__(self,window_size, matrix_size, filename, inputdir, outputdir):
        self.window_size = window_size
        self.matrix_size = matrix_size

        self.windowed_entropy = []
        self.normalized_entropy = []

        self.inputdir = inputdir
        self.filename = filename

        self.windowedoutputdir = os.path.join(outputdir,'WindowedOutputs')
        self.windowed_image_outputdir = os.path.join(outputdir, 'WindowedImageOutputs')
        self.normoutputdir = os.path.join(outputdir,'NormalizedOutputs')
        self.normalized_image_outputdir = os.path.join(outputdir, 'NormalizedImageOutputs')

    def make_dirs(self):

        if not os.path.exists(self.normoutputdir):
            os.makedirs(self.normoutputdir)

        if not os.path.exists(self.normalized_image_outputdir):
            os.makedirs(self.normalized_image_outputdir)

        if not os.path.exists(self.windowedoutputdir):
            os.makedirs(self.windowedoutputdir)

        if not os.path.exists(self.windowed_image_outputdir):
            os.makedirs(self.windowed_image_outputdir)


    def get_file_entropy(self):
        # arbitrary, but reading in 32kb chunks is a good size for efficiency

        chunksize = 32768
        file = os.path.join(self.inputdir, self.filename)

        with open(file , 'rb') as f:
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

    def save_images(self):
        self.SaveWindowedEntropyPlot()
        self.SaveWindowedEntropyPlot()

    def save_arrays(self):
        np.save(os.path.join(self.windowedoutputdir, self.filename + '.npy'), self.windowed_entropy)
        np.save(os.path.join(self.normoutputdir, self.filename + '.npy'), self.normalized_entropy)

    def SaveNormalizedEntropyPlot(self):
        FileName = os.path.join(self.normalized_image_outputdir, self.filename+'.png')
        NormEnt = self.normalized_entropy
        plt.ioff()
        plt.imshow(NormEnt, cmap='hot', interpolation='nearest')
        plt.axis('off')
        plt.savefig(FileName, bbox_inches='tight', transparent=True, pad_inches=0)

    def SaveWindowedEntropyPlot(self):
        # find the nearest square dimension
        EntList = self.windowed_entropy
        FileName = os.path.join(self.windowed_image_outputdir, self.filename+'.png')

        dimension = int(math.ceil(math.sqrt(len(EntList))))
        # pad binary to make it a square number of windows
        EntList += [0] * (dimension ** 2 - len(EntList))
        array = np.array(EntList, dtype=np.uint8)
        array = np.reshape(EntList, (dimension, dimension))
        plt.ioff()
        plt.imshow(array, cmap='hot', interpolation='nearest')
        plt.axis('off')
        plt.savefig(FileName, bbox_inches='tight', transparent=True, pad_inches=0)

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
    datasetdir = 'Datasets'
    entropy_image = EntropyDatasetBuilder(window_size, matrix_size, inputdir, datasetdir)
    feature_matrix = entropy_image.build_entropy_maps_from_exes()
