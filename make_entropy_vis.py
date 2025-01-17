import multiprocessing
import tqdm
import os
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
        np.expand_dims(np.arange(a.shape[0]-sub_window_size, step=stride_size), 0).T
    )
    return a[sub_windows]


def calcentropy(a: np.array) -> np.array:
    """
    Calculates the naive shannon entropy of an array
    a: np.array
    returns entropy
    """

    freqs, _ = np.histogram(a, bins=255)
    freqs = freqs/freqs.sum()
    freqs = freqs[freqs > 0]
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

    M = np.zeros((size, size))
    a = np.square(a)/2
    T = a.astype(int)
    for (i, j) in zip(T, T[1:]):
        M[i][j] += 1
    # for row in M:
    #     s = sum(row)
    #     if s > 0:
    #         row[:] = [f/s for f in row]
    return M


def worker(path):
    try:
        enttransitions = normalize_entropy(filetoentropy(path), 32)

    except Exception as e:
        print(e)
        print(f'entropy calculation failed on {path}')
        enttransitions = np.zeros(32, 32)
    return {'name': path, 'entropy_norm': enttransitions}


def good_data():
    base = ["/mnt/c/Windows", "/mnt/c/Program Files", "/mnt/c/Program Files (x86)", "/mnt/c/ProgramData"]
    extensions = ['.exe']
    ignore = ['servicing', '$Recycle.Bin', '$Windows.~WS']
    allfiles = []
    for folder in base:
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if not any(d == ign for ign in ignore)]
            for name in files:
                if any((name.endswith(ext) for ext in extensions)):
                    allfiles.append(root+"/"+name)
    return allfiles


if __name__ == "__main__":

    print('looking for executables')
    allfiles = good_data()
    print(f'found {len(allfiles)} executables')

    pool = multiprocessing.Pool(processes=8)
    print('starting to build entropy map')
    results = list(tqdm.tqdm(pool.imap_unordered(worker, allfiles), total=len(allfiles)))
    df = pd.DataFrame([[x['name'], x['entropy_norm'].tolist()] for x in results], columns=['name', 'image'])

    df.to_csv('./test.csv')
