# Entropyvis-malware-classification
Automatic malware classification with sliding window entropy visualization


trainingsetbuilder - this will find all the (hopefully) legitimate binaries on your windows machine and run them through the sliding window entropy calculator. Entropy is calculated for each 256 byte block in the exe itself, producing an image like this:

![Image of sliding window](https://github.com/m-m-adams/Entropyvis-malware-classification/cmd.exe-sliding.png)

This is then normalized by converting into a tmarkov transition matrix where each entropy level is considered as a state, producing something like this:

![Image of normalized entropy](https://github.com/m-m-adams/Entropyvis-malware-classification/cmd.exe-normalized.png)

Vi ran this through KNN and used the local outlier factor to detect anything that doesn't belong in the set.

Vii is running through an autoencoder instead



