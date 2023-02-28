# PyAcclaim - ASF/AMC motion data parser without hardcoding
Acclaim Motion Capture (AMC) data is a data format for storing motion capture data. While widely adopted by various motion capture systems including the Vicon motion capture systems, it appears that the existing AMC data parsers in Python involve some level of hardcoding (e.g. assumption on the order of keywords or sections). PyAcclaim aims to solve this issue through a more generic implementation, free of assumptions, such that broader variants of AMC file formats can be read without a problem.

## Installation
```bash
pip install pyacclaim
```
Additionally, if you wish to use the viewer, please install `open3d`:
```bash
pip install open3d
```

## Usage
```python
from pyacclaim import loadASF, loadAMC

asf = loadASF('test.asf')
amc = loadAMC(asf, 'test.amc')
```
Note that the test files (`test.asf` and `test.amc`) are originally from the CMU Graphics Lab Motion Capture Database (http://mocap.cs.cmu.edu/) - 'Subjet 01/Motion 01'
