# Entropyvis-malware-classification
Automatic malware classification with sliding window entropy visualization based on the paper "EntropyVis: Malware classification," by Z. Ren and G. Chen. A version directly implementing their work is in the volder Vi, the remainder of this project is improving it through applying real image classification techniques.


trainingsetbuilder - this will find all the (hopefully) legitimate binaries on your windows machine and run them through the sliding window entropy calculator. Entropy is calculated for each 256 byte block in the exe itself, producing an image like this:

![Image of sliding window](https://github.com/m-m-adams/Entropyvis-malware-classification/blob/master/images/cmd.exe-sliding.png)

This represents the binaries internal structure - areas with lots of padding are low entropy, areas of code are in the middle, and compressed areas have high entropy level

This is then normalized by converting into a transition matrix where each pixel i,j is the number of times the entropy transitioned from i to j:

![Image of normalized entropy](https://github.com/m-m-adams/Entropyvis-malware-classification/blob/master/images/cmd.exe-normalized.png)


The autoencoder learns to reconstruct legitimate images accurately, but struggles on binaries with unusual structure

![Image of legit exes](https://github.com/m-m-adams/Entropyvis-malware-classification/blob/master/images/samplerec.png)
![Image of malicious ones](https://github.com/m-m-adams/Entropyvis-malware-classification/blob/master/images/samplemal.png)


This doesn't capture all malicious binaries as many are structured much like legitimate programs, but the error distribution for malware is significantly fatter than for legitimate programs. This is a useful indicator for further investigation. The exact threshold to use would depend on the fraction of binaries you expect to be malicious

![Reconstruction error plot](https://github.com/m-m-adams/Entropyvis-malware-classification/blob/master/images/error_dist.png)


