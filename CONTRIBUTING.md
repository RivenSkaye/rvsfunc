# Contributing to rvsfunc

## Before you begin

The entire package is made with [VapourSynth](vapoursynth.com/) in mind and
it consists solely of functions for use with VapourSynth or closely related
to the things it's used for.

All of the functions contained in rvsfunc are geared towards usage for anime.
As such, if a contribution or function is _not_ intended for use with anime,
make this **abundantly clear in the docstrings**!

Is your contribution related to an [open issue](https://github.com/RivenSkaye/rvsfunc/issues)?
Then please mention `fixes #<issue number>` in the PR title or description.
Is it not there yet? Then please feel free to open one to prevent pouring time
and effort into a PR that gets denied because the functionality is readily
available elsewhere. If you've contacted me elsewhere, an issue isn't required.

## Getting started

Make sure your code is up to date with master, this is to help prevent
compatibility issues as no guarantees are made with regards to the API. Sure,
I *try* to keep it backwards compatible, but I'm not afraid of breaking it
if the need arises. People can always pin versions if they need to.

Adjust the commands as you need, these assume python 3.8 through 3.10:
```bash
$ git clone https://github.com/RivenSkaye/rvsfunc
$ python -m pip install -r ./rvsfunc/requirements-dev.txt
$ python -m pip install -e ./rvsfunc
```
Happy editing!

## Before you PR

**Types of PRs**

There's basically three types of PRs you could shoot in for this repo.
Maybe I'll end up making templates and labels at a later date, but either
way I expect the type of change to be described.

- Code and functionality, these change or add stuff to what people get when they `import rvsfunc`.
  - I expect these to include relevant changes and additions to documentation as well.
  - Don't forget to add relevant `autodoc` directives and similar to `docs/`
- Workflow changes, whenever you wish to improve, add, or change a workflow.
  - These will have to be described in detail as automation comes with risks.
  - GitHub CI can be kinda jank, so these may take some time to process.
- Documentation changes, these cause changes to what people see in [the docs](https://rvsfunc.tae.moe/).
  - These change the contents of `docs/` and/or any docstrings throughout rvsfunc.
  - These also include changes to things like [the README](./README.md) or this document.
  - You're free to change messages shown to users, like errors.
  - If possible, set up a hosted instance of doc changes on [RTD](https://readthedocs.org/) or GH Pages.

For workflow and documentation changes, feel free to offer massive overhauls.
For code changes, please try and keep API compatibility. If a function is moved or renamed,
alias it and update the diff in the README. If a function signature changes, try to use
`typing.Optional` and/or sane defaults, or send a deprecation warning for any removed arguments.

I'm open to all kinds of changes to the project so long as I see a benefit to the change being made.
As with most libraries, it's as opinionated as can be, but opinions might sway with discussion.
The main goal is to provide useful _basic_ utilities that don't have a lot of dependencies.

**Syntax and Typing**

It's important that the workflows for the repository don't break, as well as
that code formatting and typing is in order.
In order to do this, the workflows include Flake8 with some plugins and MyPy.
These are all listed in `requirements-dev.txt` so you can run them on your local machine
to ensure all is well before sending in a PR.
If the Flake8 and MyPy configurations have to be edited for the code to pass, expect
the PR to sit still while it's closely being reviewed.

**Docs**

It's also important that the docs build properly. This is _usually_ fine
if you don't add new dependencies. But there are some things that can break
Read The Docs building when you forget to list them in `docs/sphinx-requirements.txt`.
To minimize the risk of docs breaking, I ask that you list any added dependencies
that can break module or function imports in this file as well as that you
confirm builds run without errors. To verify this, either set up an RTD build,
or check this by running Sphinx locally. If you do local builds, ensure your Python
version matches what is configured for RTD to use in `readthedocs.yaml`
```bash
$ cd ./rvsfunc/docs/
$ make clean && make html
```
If any errors or warnings pop up, please resolve them _before_ submitting the PR,
or mention it in the PR and turn on the option to allow maintainers to edit your fork.
This allows me to try and help fix what's preventing the docs from building.
