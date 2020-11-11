import numpy as np
import pandas as pd

def vectorized_stride_v2(a: np.array, sub_window_size: int,
                         stride_size: int) -> np.array:
    """
    creates a sliding window view of your input array.
    sub_window_size: Size of sliding windows
    stride_size: entries between windows

    returns: a view of your array which is a.shape[0]x total windows
    """

    sub_windows = (
        np.expand_dims(np.arange(sub_window_size), 0) +
        # Create a rightmost vector as [0, V, 2V, ...].
        np.expand_dims(np.arange(a.shape[0]-sub_window_size//2, step=stride_size), 0).T
    )
    return a[sub_windows]

def calcentropy(a: np.array) -> np.array:
    """
    Calculates the naive shannon entropy of an array
    a: np.array
    returns entropy
    """

    freqs, bins = np.histogram(a, bins=255)
    freqs = freqs/freqs.sum()
    freqs = freqs[freqs>0]
    ent = freqs*np.log2(freqs)
    return -np.sum(ent)

def filetoentropy(path: str) -> np.array:
    """
    performs a sliding window entropy calculation on file
    path: path to file
    returns array of entropy values
    """
    img = np.fromfile(path, 'uint8')

    ents = np.apply_along_axis(calcentropy, 1, vectorized_stride_v2(img, 256, 128))
    return ents

def normalize_entropy(a: np.array, size: int) -> np.array:
    """
    Takes an entropy vector and normalizes it to represent
    entropy level transitions

    inputs:
    a: np.array of entropy values
    
    Outputs:
    np.array of entropy level transitions
    """

    M=np.zeros((size,size))
    T = a.astype(int)
    for (i,j) in zip(T,T[1:]):
        M[i][j] += 1
    for row in M:
        s = sum(row)
        if s > 0:
            row[:] = [f/s for f in row]
    return M

ents = filetoentropy("/mnt/c/Windows/System32/cmd.exe")
print(ents)
print(normalize_entropy(ents, 8))


