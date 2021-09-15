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
available elsewhere. _You can ignore this if you've contacted me elsewhere._

## Getting started

Make sure your code is up to date with either master, this is to help prevent
compatibility issues as no guarantees are made with regards to the API. Sure,
I *try* to keep it backwards compatible, but I'm not afraid of breaking it
if the need arises. People can always pin versions.

Adjust the commands as you need, these assume bash and python 3.8 or 3.9:
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
  - Don't forget to add relevant `autodoc` directives and similar to `docs/index.rst`
- Workflow changes, whenever you wish to improve, add, or change a workflow.
  - These will have to be described in detail as automation comes with risks.
- Documentation changes, these cause changes to what people see in [the docs](https://rvsfunc.tae.moe/).
  - These change the contents of `docs/` and/or the docstrings throughout rvsfunc.
  - These also include changes to things like [the README](./README.md) or this document.
  - You're free to change the error messages, but any other code changes go in the first point.
  - If possible, use GitHub Pages to display a build of the docs.

For workflow and documentation changes, feel free to offer massive overhauls.
For code changes, please try and keep API compatibility. _This includes alias memes._

I'm very much willing to accept changes that help me split the docs to multiple
pages. Say one per module in the package. As rvsfunc grows, I fear it will get
much too big to be easily navigatable.

**Syntax and Typing**

It's important that the workflows for the repository don't break, as well as
that code formatting and typing is all in the way I like it to be.
That means making sure you have Flake8 and the correct plugins running, as
well as MyPy. They're all listed in the `requirements-dev.txt` files for your
convenience and the configuration files are included in the repository.
Make sure they pass all checks and all should be fine.

If your changes include any modifications to existing Flake8 or MyPy rules,
the PR will not be considered or reviewed until said changes are reverted.

**Docs**

It's also important that the docs build properly. This is _usually_ fine
if you don't add new dependencies. But there are some things that can break
Read The Docs building when you forget to list them in `docs/sphinx-requirements.txt`.
To minimize the risk of docs breaking, I ask that you list any added dependencies
that can break module or function imports in this file as well as that you
confirm builds run without errors. You can check this by running:
```bash
$ cd ./rvsfunc/docs/
$ make clean && make html
```
If any errors or warnings pop up, please resolve them _before_ submitting the
PR. This is not a hard requirement, however, as I will check this as well.

## After you PR

Assuming your PR was eventually merged, future PRs should go over a bit smoother.
For one, GitHub should be running workflows over PRs of contributors, so that
means Flake8 and MyPy checking are all being handled on their end. Should save
you and me both a fair bit of effort.
