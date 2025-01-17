import os
import zipfile
import magic
import subprocess
import shutil

destination='/home/mark/File-Entropy-master/malware'


print(destination)

for filename in os.listdir(destination):
    print(filename)
    file=os.path.join(destination,filename)
    magictype = magic.from_file(file)

    if any(x in magictype for x in ['upx', 'packed', 'compressed', 'extracting']):
        packedname=os.path.join(destination,'packed-'+filename)
        os.rename(file,packedname)
        print('file was packed:',packedname)
        if 'upx' in magictype:
            print('found upx, attempting to unpack')
            # if its upx we can try to unpack it
            unpackedname = os.path.join(destination, 'upx-unpacked-' + filename)
            shutil.copyfile(packedname, unpackedname)
            try:
                subprocess.checkoutput(['upx', '-d', unpackedname])
                print('unpacked as :',unpackedname)
            except:
                # bad practice but I don't care why upx failed
                os.remove(unpackedname)
                print('failed to unpack')
