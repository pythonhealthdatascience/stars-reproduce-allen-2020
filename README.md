# STARS: Computational reproducibility of Allen et al. 2020

<!-- Status badge indicating whether CITATION file is still valid via GitHub action-->
[![Valid CITATION.cff](https://github.com/pythonhealthdatascience/stars-reproduce-allen-2020/actions/workflows/cff_validation.yaml/badge.svg)](https://github.com/pythonhealthdatascience/stars-reproduce-allen-2020/actions/workflows/cff_validation.yaml)

⚠️ ***This is a test-run for STARS work package 1. It was created to help us test out the reproduction protocol and guide creation of the [template repository](https://github.com/pythonhealthdatascience/stars_reproduction_template).*** ⚠️

This repository forms part of work package 1 on the NIHR-funded project STARS: Sharing Tools and Artefacts for Reproducible Simulations. It assesses the computational reproducibility of:

> Allen, M., Bhanji, A., Willemsen, J., Dudfield, S., Logan, S., & Monks, T. **A simulation modelling toolkit for organising outpatient dialysis services during the COVID-19 pandemic**. *PLoS One* 15, 8 (2020). https://doi.org/10.1371%2Fjournal.pone.0237628.

## Website

⭐ **Check out the website for this repository ([insert link]).** ⭐

This website is created using Quarto and hosted using GitHub Pages. It shares everything from this computational reproducibility assessment, displaying:
* The original study article and associated artefacts.
* Code and documentation from reproduction of the model.
* Evaluation of model reproduction success.
* Evaluation of the original study against guidelines for sharing research, criteria for journal reproducibility guidelines, and article reporting guidelines.
* Logbook with chronological entries detailing reproduction work.
* Final report describing the computational reproducibility assessment.

## Repository layout

```bash
├── evaluation
│   └──  ...
├── original_study
│   └──  ...
├── quarto_site
│   └──  ...
├── reproduction
│   └──  ...
├── .gitignore
├── CHANGELOG.md
├── CITATION.cff
├── LICENSE
├── README.md
├── _quarto.yml
├── citation_apalike.apa
├── citation_bibtex.bib
└── index.qmd
```

* `evaluation/` - Markdown files from the evaluation of computational reproducibility. This includes the logbook, assessment of reproduction success, and comparison of the original study materials against various guidelines, criteria and frameworks
* `original_study/` - Journal article, supplementary material, code and any other research artefacts from the original study. These items are uploaded here for reference, but should be otherwise untouched.
* `quarto_site/` - A Quarto website is used to share information from this repository (including the original study, reproduced model, and reproducibility evaluation). This folder contains any additional files required for creation of the site that do not otherwise belong in the other folders (for example, logo image files, or `.qmd` files that appropriately pull and display the original study PDF on the website)
* `reproduction/` - Reproduction of the simulation model. Once complete, this functions as a research compendium for the model, containing all the code, parameters, outputs and documentation
* `.gitignore` - Instructions for Git of which local objects should not be included in the repository
* `CHANGELOG.md` - Details changes between versions (as in GitHub releases and versions on Zenodo)
* `CITATION.cff` - Instructions for citing this repository, created using [CFF INIT](https://citation-file-format.github.io/)
* `LICENSE` - Details of the license for this work
* `README.md` - Description for this repository. You'll find a seperate README for the model within the `reproduction/` folder, and potentially also the `original_study/` folder if a README was created by the original study authors
* `_quarto.yml` - Set-up instructions for the Quarto website
* `citation_apalike.bib` - APA citation generated from CITATION.cff
* `citation_bibtex.bib` - Bibtex citation generated from CITATION.cff
* `index.qmd` - Home page for the Quarto website

## Citation

If you wish to cite this repository, please refer to the citation file `CITATION.cff`, and the auto-generated alternative format `bibtex.bib`.