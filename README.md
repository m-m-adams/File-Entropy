# File-Entropy
malware classification with sliding window entropy visualization


unzipmalware - use this to mass unzip files from the zoo (https://github.com/ytisf/theZoo) - this forms the base data set

checkifpacked - this module runs through all the malware from the zoo and tags it if its packed. 
This identification method struggles on packed malware

CalcEntropy - use this to perform the entropy visualization on the unzipped malware samples and outputs the dataset

RunKNN - does the actual KNN stuff 

