import numpy as np
from numpy import linalg as la
try: import cv2
except: pass
import os

import sys # TODO remove
import os.path # TODO remove
#from sklearn.decomposition import IncrementalPCA
#from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

def extractPatches(rgbImg, k, i):
    """
    Returns the i-th patch of the image divided into k-by-k patches, going row
    by row.
    """
    imgWidth = rgbImg.shape[0]
    imgHeight = rgbImg.shape[1]

    xSize = int(np.ceil(imgWidth / (k * 1.0)))
    ySize = int(np.ceil(imgHeight / (k * 1.0)))

    x = (i % k ) * xSize
    y = int(i/k) * ySize
    xend = min(imgWidth, x+xSize)
    yend = min(imgHeight, y+ySize)

    return rgbImg[x:xend, y:yend]

def depricated_extractPatches(rgbImg):
    width = k
    height = k

    patches = []
    while y+height < rgbImg.shape[0]:
        x = 0
        while x+width < rgbImg.shape[1]:
            patches.append(rgbImg[x:x+width, y:y+height])
            x = x + 2
        y = y + 2

    return patches

def extractFeature(patch):
    """
    Extract patch feature using multi-scale LBP descriptor.
    """
    pass

def cart2pol(x, y):
    rho = np.sqrt(x**2 + y**2)
    phi = np.arctan2(y, x)
    return(rho, phi)

def pol2cart(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return(x, y)

def s(x):
    if x >= 0:
        return 1
    else:
        return 0

def uniformity(gc, gp):

    return abs(s(gp[-1]-int(gc)) - s(gp[0] - int(gc))) + sum([abs(s(gp[i] - int(gc)) - s(gp[i-1]-int(gc))) for i in range(1, len(gp))])

def LBP(greyImg, R, P, x, y):
    """
    Extracts the LBP transform for a pixel in the image.
    """
    gc = greyImg[x, y]

    coords = np.array([ pol2cart(R, i*2*np.pi/P) for i in range(P) ], dtype=np.float32)
    coords = np.rint(coords)
    coords = coords.astype(int)

    res = 0
    gp = []
    for i, px in enumerate(coords):
        # Looks like this is flipped but it actually needs to be like this.
        g = 0
        try:
            g = greyImg[x+px[1], y+px[0]]
        except Exception:
            pass

        gp.append(g)
        res = res + s(int(g) - int(gc))*2**i

    return (res, gc, gp)

def createIndex():
    index = {}
    i = 0

    def I(x):
        if x in index:
            return index[x]
        else:
            index[x] = len(index)
            return index[x]

    return I

def mLBP(greyImg, R, P, x, y, I):
    lbp, gc, gp = LBP(greyImg, R, P, x, y)
    if uniformity(gc, gp) <= 2:
        return I(lbp)
    else:
        return (P-1)*P+2


def H(m, R, P, I):
    """
    Calculates regional LBP histogram for the subregion m and radius r.
    """
    h = np.zeros((1, (P-1)*P+2), dtype=int)

    for i, row in enumerate(m):
        for j, px in enumerate(row):
            res = mLBP(m, R, P, i, j, I)
            if not res == 58:
                h[0][res] = h[0][res] + 1
    return h

def F(m, R, P, I):
    """
    Calculates multiresolution regional facedescriptor by concatenating histograms
    for all radii 1..R.
    """
    f = np.zeros((R, (P-1)*P+2))

    for r in range(1, R+1):
        h = H(m, r, P, I)
        f[r-1] = h
    return f

def FJ(images, j, R, P, k, I, name=None):
    """
    Calculates regional facedescriptors F for region j of all images.
    """
    if not name is None:
        if os.path.exists('savedMatrix/Fj'+str(j)+name+'.npy'):
            fj = np.load('savedMatrix/Fj'+str(j)+name+'.npy')
            return fj

    FJ = []
    i = 0
    for img in images:
        img = img.astype(np.uint8)

        patch = extractPatches(img, k, j)

        FJ.append(np.reshape(F(patch, R, P, I), 580))

        i += 1
        print "FJ " + str(i) + " " + str(j) + " " + str(name) 

    if not name is None:
        print "Trying to save"
        #np.save('savedMatrix/Fj' + str(j)+name, FJ)
    return FJ

def WJlda(images, labels, j, R, P, k, I, name=''):
    """
    Calculates a transformation matrix based on PCA such that  98% of the signal
    are retained and after that applies LDA to transform the data.
    """

    fj = FJ(images, j, R, P, k, I, name)
    #np.save('savedMatrix/Fj' + str(j)+name, fj)

    #print fj.shape

    print "Fj shape" + str(fj.shape)
    #print fj[2][100:120]

    wPCA = PCA(fj)

    #print wPCA
    #return wPCA

    #wLDA = LDA(fj, labels)
    wLDA = LDA(DJ(wPCA, fj), labels)
    #print wLDA

    return wPCA.dot(wLDA)

def DJ(W, FJ):
    """
    Transform FJ into LDA space
    """
    return FJ.dot(W)

def imageOpenAndNormalize(imagePath):
    """
    OLD TODO Normalize and center the image according to CSU standard
    """
    image = cv2.imread(imagePath)

    rgbImg = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    aligner = GFAlign(None)
    rects = aligner.detectAll(rgbImg)

    (x, y, w, h) = aligner.rect2BoundingBox(rects[0])

    grayImg = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thumbnail = grayImg[y:y+h,x:x+w]
    thumbnail = cv2.resize(thumbnail, (resizeHeight, resizeWidth))

    return thumbnail

def createFileList(partitionName, printFound=False):
    """
    Find images with changed names for the from the CSU training or testing sets
    """
    partitionsPath = './colorferet/'
    imagePath1 = './colorferet/output/'
    imagePath2 = './colorferet/colorferet/colorferet/dvd2/data/images/'

    imgCount = 0
    filename = partitionsPath + partitionName + '.txt'
    print filename
    num_lines = sum(1 for line in open(filename))

    fileList = []

    with open(filename, 'r') as fp:
        for line in fp:
            image = line.split()
            for img in image:
                imgFile = img[:-3] + 'pgm'

                if os.path.exists(imagePath1 + imgFile):
                    imagePath = imagePath1 + imgFile
                elif os.path.exists(imagePath2 + imgFile):
                    imagePath = imagePath2 + imgFile
                else:
                    print(img)
                    print(str(imgFile) + " File not found")
                    continue
                if printFound:
                    print("Found: " + imgFile + " Progress: " +str(round(100.0*imgCount/495, 1)) + "%")
                imgCount += 1
                fileList.append(imagePath)
    print "Images found " + partitionName + " " + str(imgCount)
    return fileList;

def PCA(data):

    # Covariance matrix
    #data = (data - np.mean(data, axis=0)) / np.std(data, axis=0) # TODO Check
    cov = np.cov(data, rowvar=False)
    #mu = np.mean(data, axis=0)
    #cov = np.cov((data - mu), rowvar=False)

    #print cov.shape
    #print "PCA cov symmetric? " + str((cov.T == cov).all())

    # Compute eigenvectors
    eigValues, eigVectors = la.eig(cov)
    eigSize = eigValues.shape
    normV = eigValues / np.sum(eigValues)

    # Sort the eigenvectors
    sortedV = np.argsort(normV)
    sortedV = sortedV[: :-1]

    # Find the most important eigenvectors
    important = normV[sortedV[0]]
    w = eigVectors[:, sortedV[0]];
    i = 1;
    while (important < 0.98 and i < eigSize[0]) or i < 2:
        important += normV[sortedV[i]]
        w = np.vstack((w, eigVectors[:, sortedV[i]]));
        i += 1;

    print("PCA Eigenvectors " + str(i))


    #for i in range(0, eigSize[0]):
    #    eigVectorsA = np.real(eigVectors[: ,i])
    #    eigValuesA = np.real(eigValues[i])
    #    #eigValues = np.diag(eigValues)
    #    print "ResPCA " + str(i) + " " + str((np.isclose(cov.dot(eigVectorsA), eigValuesA.dot(eigVectorsA), 1).all()))

    return np.real(w.T)

def LDA(data, labels):
    feat = data.shape[1]

    print data.shape
    print labels

    labelsArgSorted = np.argsort(labels)
    for i in labelsArgSorted:
        print labels[i]

    

    # Calculate mean

    mu = np.mean(data, axis=0, dtype='float64')

    sw = np.zeros((feat, feat), dtype='float64')
    sb = np.zeros((feat, feat), dtype='float64')



    muClass = np.zeros((1, feat), dtype='float64')
    dataClass = np.zeros((0, feat), dtype='float64')
    label = labels[0]
    objects = 0
    for idx in range(0, data.shape[0]):
        if (not label == labels[idx]) or idx == data.shape[0]-1:
            if idx == data.shape[0]-1:
                muClass += data[idx]
                dataClass = np.vstack((dataClass, data[idx]))
                objects += 1

            label = labels[idx]
            muClass = muClass / objects
            sw += ((dataClass - muClass).T.dot((dataClass - muClass)))
            sb += objects * (muClass - mu) * (muClass - mu).reshape(feat, 1);
            dataClass = np.zeros((0, feat), dtype='float64')
            muClass = np.zeros((1, feat), dtype='float64')
            objects = 0

        objects += 1
        muClass += data[idx]
        dataClass = np.vstack((dataClass, data[idx]))

    #print "w " + str((sb.T == sb).all())
    #print "b " + str((sw.T == sw).all())

    print "sw"
    print sw
    print "sb"
    print sb


    invMatrix = la.inv(sw).dot(sb)

    #print "inv " + str((invMatrix.T == invMatrix).all())
    #print "invClose " + str((np.isclose(invMatrix.T, invMatrix)).all())

    eig, eigV = la.eig(invMatrix)

    #print "Res " + str((np.isclose(invMatrix.dot(eigV), eig.dot(eigV)).all()))

    eig = np.real(eig)
    print eig

    # Get more Eigenvectors
    # Sort the eigenvectors
    normV = eig / np.sum(eig)
    eigSize = eigV.shape
    sortedV = np.argsort(normV)
    sortedV = sortedV[: :-1]

    # Find the most important eigenvectors
    important = normV[sortedV[0]]
    w = eigV[:, sortedV[0]];
    i = 1;
    print important
    while (important < 1 - 1E-4 and i < eigSize[0]) :#or i < 100:
        print normV[sortedV[i]]
        important += normV[sortedV[i]]
        w = np.vstack((w, eigV[:, sortedV[i]]));
        i += 1;

    print "LDA Eigenvalues  " + str(i)

    #for i in range(0, eigSize[0]):
    #    eigVectorsA = np.real(eigV[: ,i])
    #    eigValuesA = np.real(eig[i])
        #eigValues = np.diag(eigValues)
    #    bb = (np.isclose(invMatrix.dot(eigVectorsA), eigValuesA.dot(eigVectorsA)).sum())
    #    print "ResLDA " + str(i) + " " + str(bb)
        #if bb:
            #print invMatrix.dot(eigVectorsA)  - eigValuesA.dot(eigVectorsA)
            #print invMatrix.dot(eigVectorsA) 
            #print eigValuesA.dot(eigVectorsA)

            #raw_input("Press key")



    return np.real(w.T)