# Entropyvis-malware-classification
Automatic malware classification with sliding window entropy visualization


unzipmalware - use this to mass unzip files from the zoo (https://github.com/ytisf/theZoo) - this forms the base data set

checkifpacked - this module runs through all the malware from the zoo and tags it if its packed. 
This identification method struggles on packed malware

CalcEntropy - use this to do the entropy visualization on the unzipped malware samples to create the features and output the dataset

RunKNN - does the actual KNN stuff 
