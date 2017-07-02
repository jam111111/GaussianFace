# GaussianFace
Implementation of the GaussianFace algorithm for TU Delft IN4393 Computer Vision 2016/2017

The repository does not contain the dataset of images. The data can be places in colorferet/output/ and is expected to be normalized images from the gray FERET dataset of size 150x130pixels.

To run the system install and create a virtual environment with Python 2.7. 
Please note that creating the F matrix for a lot of images as required in training and testing takes a long time.

$ pip install virtualenv
$ virtualenv project

Activate and configure virtualenv
$ source project/bin/activate (Linux)
$ pip install -r requirements.txt

To run training and testing: (Requires FERET normalized images and takes a long time)
The normalized feret images should be placed in /colorferet/output in pgm format (examplename: 00001fa010_930831.pgm).
Train the LDA transformation matrix
	$ python -m demos.trainWLDA 
Test on the testdata
	$ python -m demos.testAlgorithm 

Test the LBP faces
        $ python -m demos.lbpfaces <imgpath>
