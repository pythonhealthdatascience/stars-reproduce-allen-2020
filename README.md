# Reproducing Monks et al. 2016

⚠️ ***This repository is a test-run for STARS work package 1 (and is not one of the six reproduced DES models). It was created to help us test out the reproduction protocol and guide creation of the template, https://github.com/pythonhealthdatascience/stars_reproduction_template.*** ⚠️

This repository forms part of work package 1 on the NIHR-funded project STARS: Sharing Tools and Artefacts for Reproducible Simulations. It assesses the computational reproducibility of:

> Monks, T., Worthington, D., Allen, M., Pitt, M., Stein, K., & James, M. A. **A modelling tool for capacity planning in acute and community stroke services**. *BMC Health Services Research* 16, 530 (2016). https://doi.org/10.1186/s12913-016-1789-4

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
├── _quarto.yml
├── .gitignore
├── index.qmd
├── LICENSE
└── README.md
```

* `evaluation/` - Markdown files from the evaluation of computational reproducibility. This includes the logbook, assessment of reproduction success, and comparison of the original study materials against various guidelines, criteria and frameworks
* `original_study/` - Journal article, supplementary material, code and any other research artefacts from the original study. These items are uploaded here for reference, but should be otherwise untouched.
* `quarto_site/` - A Quarto website is used to share information from this repository (including the original study, reproduced model, and reproducibility evaluation). This folder contains any additional files required for creation of the site that do not otherwise belong in the other folders (for example, logo image files, or `.qmd` files that appropriately pull and display the original study PDF on the website)
* `reproduction/` - Reproduction of the simulation model. Once complete, this functions as a **research compendium** for the model, containing all the code, parameters, outputs and documentation
* `_quarto.yml` - Set-up instructions for the Quarto website
* `.gitignore` - Instructions for Git of which local objects should not be included in the repository
* `index.qmd` - Home page for the Quarto website
* `LICENSE` - Details of the license for this work
* `README.md` - Description for this repository. You'll find a seperate README for the model within the `reproduction/` folder, and potentially also the `original_study/` folder if a README was created by the original study authors