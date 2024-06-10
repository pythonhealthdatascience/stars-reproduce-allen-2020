# Source: https://github.com/TomMonks/treatment-centre-sim/blob/main/Dockerfile

# Use publicly available Linux-Miniconda image
# start with miniconda image
FROM continuumio/miniconda3:latest

# Create and set the working directory to the container make copy simpler
RUN mkdir /home/code
WORKDIR /home/code

# Copy all files across to container
COPY . /home/code

# Copy jupyter config file
COPY jupyter_notebook_config.py /root/.jupyter/jupyter_notebook_config.py

# Install anaconda, conda-forge and pip dependencies
RUN conda update conda && conda env create -f environment.yaml && conda clean -afy 

# Make RUN commands use the new environment (not really necessary here)...
SHELL ["conda", "run", "-n", "covid19", "/bin/bash", "-c"]

# Declare port used by jupyter-lab
EXPOSE 80

# Launch JupyterLab and open the reproduction notebook
CMD jupyter-lab /home/code/reproduction.ipynb