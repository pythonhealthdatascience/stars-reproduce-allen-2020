# COVID-19 Dialysis Service Delivery Model

**Article:** Allen, M., Bhanji, A., Willemsen, J., Dudfield, S., Logan, S., & Monks, T. **A simulation modelling toolkit for organising outpatient dialysis services during the COVID-19 pandemic**. *PLoS One* 15, 8 (2020). <https://doi.org/10.1371%2Fjournal.pone.0237628>.

**Source code:** <https://zenodo.org/records/3760626>.

**Plain english summary:**

**Model scope:**

**Reproduction specs:**

## Steps to reproduce results

### Part 1. Set up environment

There are two options: using conda to install the provided virtual environment on your local machine, or using a docker image containing all the code and the virtual environment.

**Conda environment:** To use the provided conda environment, run the following in a terminal

```
conda env create -f environment.yaml
```

You can use this environment in your preferred IDE, such as VSCode. To use the browser-based JupyterLab, run the following:

```
conda activate covid19
jupyter-lab
```

**Docker:** To use the Docker image, you will need `docker` installed on your local machine. You can then obtain the image by either:

* Pulling a pre-built image from the GitHub container registry by running `docker pull ghcr.io/pythonhealthdatascience/covid19:latest`, or
* Building the image locally from the Dockerfile by running `docker build --tag covid19 .`

To run the image, you should then issue the following commands in your terminal:

```
docker run -it -p 8080:80 --name covid19_docker covid19
conda activate covid19
jupyter-lab
```

Then open your browser and go to <https://localhost:8080>. This will open Jupyterlab within the reproduction/ directory.

### Part 2. Running the model

The three items in the scope are all produced by running `reproduction.ipynb`.

Run `pytest` (make sure you current directory is the `reproduction/` folder) to check that model results from your run are as expected.
