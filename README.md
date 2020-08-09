# Umbrella

> An umbrella protects you when the cloud falls into raindrops.

Umbrella creates local backups for all the Git repos you cared about. An ex-employee deletes all the branches? Service providers go down? Repositories being taken down by DMCA? Umbrella gets you covered.

**Note: this piece of software is in early development.**

## Requirements

* *nix operating system
* `git` and `git-lfs` installed
* Python 3.8 or later

## Usage

TBD.

## Snapshots and Incremental Backups

Umbrella does not offer any form of snapshot or incremental backup because I don't want to rebuild square wheels. You can use the functionalities provided by your filesystem (e.g. [ZFS](https://zfsonlinux.org/) or [Btrfs](https://btrfs.wiki.kernel.org/index.php/Main_Page)) or 3rd party backup solutions (e.g. [Borg](https://borgbackup.readthedocs.io/) or [Duplicati](https://www.duplicati.com/)) to do this.

## TODO:

* submodules
