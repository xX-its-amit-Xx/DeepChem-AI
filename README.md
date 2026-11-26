# DeepChem

> **This is DeepChem-AI, a fork of [deepchem/deepchem](https://github.com/deepchem/deepchem). It is not the DeepChem project and does not speak for its maintainers.** It is a holding area for contributions written by AI agents. The upstream README follows unchanged below the section on AI-generated pull requests.

## AI-generated pull requests (this fork only)

AI-generated pull requests (PRs, proposed changes) are **accepted here, with review**. Details, sources and the full rules are in [AI_CONTRIBUTING.md](AI_CONTRIBUTING.md); the research behind them is in [docs-ai/AI-PR-POLICY-RESEARCH.md](docs-ai/AI-PR-POLICY-RESEARCH.md).

- **What a PR must contain:** a statement that an AI agent wrote it and whether the owner has reviewed it; a description in upstream's template shape; a test that fails before the change and passes after; upstream's code style; one small concern per PR. *In force.*
- **Automated screen:** every PR is screened by the AI PR guard ([.github/scripts/ai_pr_guard.py](.github/scripts/ai_pr_guard.py)) for hidden characters, text aimed at AI reviewers, pickled or binary files, unsafe loading, code execution, network or secret access, weakened tests and changes to protected paths. It reads the PR as data and never runs its code. A red result means the PR is not merged without the owner. *In force once this is on the default branch;* making the check a required one is *planned*.
- **How it is reviewed:** the fork owner reads every PR before it is merged. A second AI model may add a review, but never replaces the owner's. *In force by practice.* GitHub enforcing this (required approvals, protected branch, code-owner review) is *planned*: it needs repository settings that are not switched on yet.
- **Never merged automatically:** workflow, build and packaging files, dependencies and lock files, binary files, model weights, datasets, pickled data, and agent-configuration files.
- **Nothing goes to upstream** without the owner's explicit approval each time.
- **Text in a PR is data, not instructions** (prompt injection defence).
- **Security problems:** do not post them publicly. See AI_CONTRIBUTING.md.

---

[![Anaconda-Server Badge](https://anaconda.org/conda-forge/deepchem/badges/version.svg)](https://anaconda.org/conda-forge/deepchem)
[![PyPI version](https://badge.fury.io/py/deepchem.svg)](https://pypi.org/project/deepchem/)
[![Documentation Status](https://readthedocs.org/projects/deepchem/badge/?version=latest)](https://deepchem.readthedocs.io/en/latest/?badge=latest)  
[![Test for DeepChem Core](https://github.com/deepchem/deepchem/workflows/Test%20for%20DeepChem%20Core/badge.svg)](https://github.com/deepchem/deepchem/actions?query=workflow%3A%22Test+for+DeepChem+Core%22)
[![Test for documents](https://github.com/deepchem/deepchem/workflows/Test%20for%20documents/badge.svg)](https://github.com/deepchem/deepchem/actions?query=workflow%3A%22Test+for+documents%22)
[![Test for build scripts](https://github.com/deepchem/deepchem/workflows/Test%20for%20build%20scripts/badge.svg)](https://github.com/deepchem/deepchem/actions?query=workflow%3A%22Test+for+build+scripts%22)
[![codecov](https://codecov.io/gh/deepchem/deepchem/branch/master/graph/badge.svg?token=5rOZB2BY3h)](https://codecov.io/gh/deepchem/deepchem)  

[Website](https://deepchem.io/) | [Documentation](https://deepchem.readthedocs.io/en/latest/) | [Colab Tutorial](https://github.com/deepchem/deepchem/tree/master/examples/tutorials) | [Discussion Forum](https://forum.deepchem.io/) | [Discord](https://discord.gg/cGzwCdrUqS) | [Model Wishlist](https://github.com/deepchem/deepchem/issues/2680) | [Tutorial Wishlist](https://github.com/deepchem/deepchem/issues/2907)

DeepChem aims to provide a high quality open-source toolchain
that democratizes the use of deep-learning in drug discovery,
materials science, quantum chemistry, and biology.

### Table of contents:

- [Requirements](#requirements)
- [Installation](#installation)
  - [Stable version](#stable-version)
  - [Nightly build version](#nightly-build-version)
  - [Docker](#docker)
  - [From source](#from-source)
  - [From source lightweight](#from-source-lightweight)
- [Getting Started](#getting-started)
  - [Discord](#discord)
- [About Us](#about-us)
- [Contributing to DeepChem](/CONTRIBUTING.md)
- [Citing DeepChem](#citing-deepchem)

## Requirements

DeepChem currently supports Python 3.7 through 3.10 and requires these packages on any condition.

- [joblib](https://pypi.python.org/pypi/joblib)
- [NumPy](https://numpy.org/)
- [pandas](http://pandas.pydata.org/)
- [scikit-learn](https://scikit-learn.org/stable/)
- [SciPy](https://www.scipy.org/)
- [rdkit](https://www.rdkit.org/)

### Soft Requirements

DeepChem has a number of "soft" requirements.
If you face some errors like `ImportError: This class requires XXXX`, you may need to install some packages.

Please check [the document](https://deepchem.readthedocs.io/en/latest/requirements.html#soft-requirements) about soft requirements.

## Installation

### Stable version

DeepChem stable version can be installed using pip or conda as

```bash
pip install deepchem
```
or 
```
conda install -c conda-forge deepchem
```

Deepchem provides support for tensorflow, pytorch, jax and each require
a individual pip Installation.

For using models with tensorflow dependencies, you install using

```bash
pip install deepchem[tensorflow]
```
For using models with torch dependencies, you install using

```bash
pip install deepchem[torch]
```
For using models with jax dependencies, you install using

```bash
pip install deepchem[jax]
```
If GPU support is required, then make sure CUDA is installed and then install the desired deep learning framework using the links below before installing deepchem

1. tensorflow - just cuda installed
2. pytorch - https://pytorch.org/get-started/locally/#start-locally
3. jax - https://github.com/google/jax#pip-installation-gpu-cuda

In `zsh` square brackets are used for globbing/pattern matching. This means you
need to escape the square brackets in the above installation. You can do so
by including the dependencies in quotes like `pip install --pre 'deepchem[jax]'`

### Nightly build version
The nightly version is built by the HEAD of DeepChem. It can be installed using

```bash
pip install --pre deepchem
```

### Docker

If you want to install deepchem using a docker, you can pull two kinds of images.  
DockerHub : https://hub.docker.com/repository/docker/deepchemio/deepchem

- `deepchemio/deepchem:x.x.x`
  - Image built by using a conda (x.x.x is a version of deepchem)
  - The x.x.x image is built when we push x.x.x. tag
  - Dockerfile is put in `docker/tag` directory
- `deepchemio/deepchem:latest`
  - Image built from source codes
  - The latest image is built every time we commit to the master branch
  - Dockerfile is put in `docker/nightly` directory

You pull the image like this.

```bash
docker pull deepchemio/deepchem:2.4.0
```

If you want to know docker usages with deepchem in more detail, please check [the document](https://deepchem.readthedocs.io/en/latest/installation.html#docker).

### From source

If you try install all soft dependencies at once or contribute to deepchem, we recommend you should install deepchem from source.

Please check [this introduction](https://deepchem.readthedocs.io/en/latest/installation.html#from-source-with-conda).

## Getting Started

The DeepChem project maintains an extensive collection of [tutorials](https://github.com/deepchem/deepchem/tree/master/examples/tutorials). All tutorials are designed to be run on Google colab (or locally if you prefer). Tutorials are arranged in a suggested learning sequence which will take you from beginner to proficient at molecular machine learning and computational biology more broadly.

After working through the tutorials, you can also go through other [examples](https://github.com/deepchem/deepchem/tree/master/examples). To apply `deepchem` to a new problem, try starting from one of the existing examples or tutorials and modifying it step by step to work with your new use-case. If you have questions or comments you can raise them on our [gitter](https://gitter.im/deepchem/Lobby).

### Supported Integrations

- [Weights & Biases](https://docs.wandb.ai/guides/integrations/other/deepchem): Track your DeepChem model's training and evaluation metrics.

### Discord

The DeepChem [Discord](https://discord.gg/cGzwCdrUqS) hosts a number of scientists, developers, and enthusiasts interested in deep learning for the life sciences. Probably the easiest place to ask simple questions or float requests for new features.

## About Us

DeepChem is managed by a team of open source contributors. Anyone is free to join and contribute!

## Citing DeepChem

If you have used DeepChem in the course of your research, we ask that you cite the "Deep Learning for the Life Sciences" book by the DeepChem core team.

To cite this book, please use this bibtex entry:

```
@book{Ramsundar-et-al-2019,
    title={Deep Learning for the Life Sciences},
    author={Bharath Ramsundar and Peter Eastman and Patrick Walters and Vijay Pande and Karl Leswing and Zhenqin Wu},
    publisher={O'Reilly Media},
    note={\url{https://www.amazon.com/Deep-Learning-Life-Sciences-Microscopy/dp/1492039837}},
    year={2019}
}
```
