# Massively Parallel Importance Sampling
Code for the paper "Using Autodiff to Estimate Posterior Moments, Marginals and Samples", published at UAI 2024 ([https://arxiv.org/abs/2310.17374](https://arxiv.org/abs/2310.17374)).

## Setup

In order to run the experiments we must first set up the massively parallel library, `alan`, and install the necessary dependencies.

```
pip install -e ./
```

This should install all necessary pip modules va src/alan.egg-info/requires.txt.
But note in particular that this includes Functorch (https://github.com/facebookresearch/functorch), which on MacOS may need you to run `export MACOSX_DEPLOYMENT_TARGET=10.9` before installation.

## Source-Term Trick

The experiments make use of the source-term trick described in the paper via the Sample class.
In comparison, the global IS and non-HMC iterative results use the SampleNonMP class.

## Data

The data files needed to run the experiments are already included in the `experiments/[model_name]/data/` directories, however, if you wish to generate the data files yourself, you can do so by following the instructions below.

### NYC Bus Breakdown
The NYC Bus Breakdown data can be generated by first downloading the dataset as a .csv file from
https://data.cityofnewyork.us/Transportation/Bus-Breakdown-and-Delays/ez4e-fazm into `experiments/bus_breakdown/` and then calling

```
python make_data.py
```
from inside `experiments/bus_breakdown/`.

### Chimpanzee Prosociality
The full Chimpanzee Prosociality dataset is already included as the file `experiments/chimpanzees/data/chimpanzees.csv`, however, it can be downloaded from
https://github.com/rmcelreath/rethinking/blob/master/data/chimpanzees.csv
Similarly, the preprocessed data is already included in `experiments/chimpanzees/data` but can be produced again by calling

```
python make_data.py
```
from inside `experiments/chimpanzees/`.

### MovieLens
The MovieLens 100K dataset can be downloaded and the data files can be generated using the following commands (from within the `experiments/movielens/` directory):

```
wget https://files.grouplens.org/datasets/movielens/ml-100k.zip
unzip ml-100k.zip
python make_data.py
```

### Bird Occupancy
The Bird Occupancy dataset can be generated by first downloading the full dataset as a zip file `2022Release_Nor.zip` from 
https://www.sciencebase.gov/catalog/item/625f151ed34e85fa62b7f926 and extracting that into `experiments/occupancy/` and then calling

```
python make_data.py
```
from inside `experiments/occupancy/`.


## Experiments
The results used in the paper are already included in `experiments/[model_name]/results/moments/`, however, the experiments can be executed to obtain new results as follows.

### MP IS & Global IS
The MP IS and global IS experiments use the file `experiments/runner_moments_IS.py` along with the arguments specified (along with default values) in the Hydra config file `experiments/config/moments_IS_conf.yaml`.
The full list of calls to this runner file used in the results presented in the paper are as follows:

```
python runner_moments_IS.py model=bus_breakdown method=mpis fake_data=True
	python runner_moments_IS.py model=bus_breakdown method=mpis fake_data=False
	python runner_moments_IS.py model=bus_breakdown method=global_is fake_data=True
	python runner_moments_IS.py model=bus_breakdown method=global_is fake_data=False

	python runner_moments_IS.py model=chimpanzees method=mpis fake_data=True
	python runner_moments_IS.py model=chimpanzees method=mpis fake_data=False
	python runner_moments_IS.py model=chimpanzees method=global_is fake_data=True
	python runner_moments_IS.py model=chimpanzees method=global_is fake_data=False

	python runner_moments_IS.py model=movielens method=mpis fake_data=True
	python runner_moments_IS.py model=movielens method=mpis fake_data=False
	python runner_moments_IS.py model=movielens method=global_is fake_data=True
	python runner_moments_IS.py model=movielens method=global_is fake_data=False

	python runner_moments_IS.py model=occupancy method=mpis reparam=False fake_data=True
	python runner_moments_IS.py model=occupancy method=mpis reparam=False fake_data=False
	python runner_moments_IS.py model=occupancy method=global_is reparam=False fake_data=True
	python runner_moments_IS.py model=occupancy method=global_is reparam=False fake_data=False	
```

### Iterative Methods

The VI, IWAE and RWS experiments use the file `experiments/runner_moments_iterative.py` along with the arguments specified (along with default values) in the Hydra config file `experiments/config/moments_iterative_conf.yaml`.
The full list of calls to this runner file used in the results presented in the paper are as follows:

```
python runner_moments_iterative.py model=bus_breakdown method=vi
python runner_moments_iterative.py model=bus_breakdown method=vi fake_data=True
python runner_moments_iterative.py model=bus_breakdown K=10 method=vi
python runner_moments_iterative.py model=bus_breakdown K=10 method=vi fake_data=True
python runner_moments_iterative.py model=bus_breakdown K=10 method=rws
python runner_moments_iterative.py model=bus_breakdown K=10 method=rws fake_data=True

python runner_moments_iterative.py model=chimpanzees method=vi
python runner_moments_iterative.py model=chimpanzees method=vi fake_data=True
python runner_moments_iterative.py model=chimpanzees K=10 method=vi
python runner_moments_iterative.py model=chimpanzees K=10 method=vi fake_data=True
python runner_moments_iterative.py model=chimpanzees K=10 method=rws
python runner_moments_iterative.py model=chimpanzees K=10 method=rws fake_data=True

python runner_moments_iterative.py model=movielens method=vi
python runner_moments_iterative.py model=movielens method=vi fake_data=True
python runner_moments_iterative.py model=movielens K=10 method=vi
python runner_moments_iterative.py model=movielens K=10 method=vi fake_data=True
python runner_moments_iterative.py model=movielens K=10 method=rws
python runner_moments_iterative.py model=movielens K=10 method=rws fake_data=True

python runner_moments_iterative.py model=occupancy K=10 method=rws reparam=False
python runner_moments_iterative.py model=occupancy K=10 method=rws reparam=False fake_data=True
```

## Making Plots
Similarly, the final plots presented in the paper already exist in `experiments/plotting/plots/`, but can be remade from the existing/any new results by calling 

```
python make_plots.py
```
from inside `experiments/plotting`.

The figures are saved in experiments/plotting/plots, and the filenames correspond to the figures in the paper as follows:

Fig. 1  = IS_per_K.pdf
Fig. 2  = IS_per_K_time.pdf
Fig. 3  = summary.pdf 
Fig. 8  = VI_summary.pdf 
Fig. 9  = IWAE_summary.pdf 
Fig. 10 = RWS_summary.pdf
## APPENDIX
### HMC
Although we found HMC far too slow a method to produce comparable results against the other methods, we provide implementations here for completeness.
#### Setup
Further modules must be installed in order to run the HMC experiments.
These have not been included by default in the main requires.txt file as not only are they unnecessary for reproducing the results in the paper, but also as the authors have experienced issues using the necessary versions of CUDA-enabled JAX and PyTorch simultaneously.
These additional modules are: pymc, jaxlib, blackjax and JAX 0.4.23, the first three of which are listed in HMC/HMC_requires.txt and can be installed via
```
pip install -r HMC/HMC_requires.txt
```
whilst the installation of JAX depends on your CUDA version, e.g. for CUDA 12
```
pip install --upgrade "jax[cuda12_local]" -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html`
```

#### Experiments
The HMC experiments use the file `experiments/runner_moments_HMC.py` along with the arguments specified (along with default values) in the Hydra config file `experiments/config/moments_HMC_conf.yaml`.
To generate results for the three compatible datasets/models, you would run the script as follows.
```
python runner_moments_HMC.py model=bus_breakdown
python runner_moments_HMC.py model=bus_breakdown fake_data=True

python runner_moments_HMC.py model=chimpanzees
python runner_moments_HMC.py model=chimpanzees fake_data=True

python runner_moments_HMC.py model=movielens
python runner_moments_HMC.py model=movielens fake_data=True
```
