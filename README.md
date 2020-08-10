# Umbrella

> An umbrella protects you when the cloud falls into raindrops.

Umbrella creates local backups for all the Git repos you cared about. An ex-employee deletes all the branches? Service providers go down? Repositories being taken down by DMCA? Umbrella gets you covered.

## Requirements

* Windows or \*nix operating system
* `git` and `git-lfs` installed
* Python 3.8 or later

## Usage

Back up a single repo:

```shell
python3 setup.py install
umbrella https://github.com/Jamesits/umbrella.git /tmp/umbrella
```

Back up a batch of repos:

1. Create a config file: [config.yaml](doc/example/config.yaml)
1. `umbrella --config config.yaml`

### Known Issues

* Integrated auth doesn't work for git (but works for providers), please log in yourself on the backup computer
* Restore is not done yet; you might need to manually restore for now

### Incremental Backups

Umbrella does not offer any form of incremental backup because I don't want to rebuild square wheels. You can use the functionalities provided by your filesystem (e.g. [ZFS](https://zfsonlinux.org/) or [Btrfs](https://btrfs.wiki.kernel.org/index.php/Main_Page)) or 3rd party backup solutions (e.g. [Borg](https://borgbackup.readthedocs.io/) or [Duplicati](https://www.duplicati.com/)) to do this.

## Development Notes

```shell
pipenv shell
python3 -m umbrella
```
