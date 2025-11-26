```

                       ████████ ██   ██ ███████ ██████  ███    ███  ██████  ███████
                          ██    ██   ██ ██      ██   ██ ████  ████ ██    ██ ██     
                          ██    ███████ █████   ██████  ██ ████ ██ ██    ██ ███████
      ██████              ██    ██   ██ ██      ██   ██ ██  ██  ██ ██    ██      ██
     ██    ██             ██    ██   ██ ███████ ██   ██ ██      ██  ██████  ███████
    ██▄▄▄▄▄▄██                                                                     
 ████▄▄▄▄▄▄▄▄████                                    █▀▄ █▀█ ▀█▀ █▀▀ ▀█▀ █   █▀▀   
██              ██                                   █ █ █ █  █  █▀▀  █  █   █▀▀   
██               █                                   ▀▀  ▀▀▀  ▀  ▀   ▀▀▀ ▀▀▀ ▀▀▀   
██               █            ░                                                    
██               █         ░░░░                      █▄█ █▀█ █▀█ █▀█ █▀▀ █▀▀ █▀▄   
██               █       ░░░░░░  ░                   █ █ █▀█ █ █ █▀█ █ █ █▀▀ █▀▄   
██               █       ░░     ░░░                  ▀ ▀ ▀ ▀ ▀ ▀ ▀ ▀ ▀▀▀ ▀▀▀ ▀ ▀   
██               █            ░░░                                                  
██               █           ░░                                                    
██               █                                                                 
██               █    ▄▄▄        ▄▄▄                                               
██               █    █  ▀▀▀▀▀▀▀▀  █                                               
██               █     █          █                                                
██               █      █        █                                                 
██               █       ████████                                                  
██████████████████                                                                 
```

tdm is a dotfile manager focused on ergonomics and flexibility.

## Installation

1. Download the `uv` package manager.
2. Run 
```bash
make build
```
3. Symlink the binary located in `bin/` so it is in the path.

## Docs

tdm uses a git repository to version your dotfiles. These dotfiles are deployed across your system via symlinks.
When deploying a symlink tdm backups the original version of the file. When tdm vacates, it restores these locations to previous state.
tdm allows for different *profiles*, these enable you to maintain different versions of your dotfiles and also to deploy them differently.

### How to get started

First create your dotfile repository with the command.
```bash
tdm init PATH
```

If you already have the git remote for your repo ready (by for example creating an empty GitHub/GitLab repository) run instead:

```bash
tdm init -g PATH 
```

You will be prompted to add the remote.

Inside of this newly created directory you will see these four children.

```
dotfiles_repo/
├── bin
├── config.toml
├── files
└── forks
```
To summarize:
- `bin`: For your scripts, when you want to run bootstrap scripts tdm looks here to find the executable you specified.
- `config.toml`: Your configuration file.
- `files`: Here are the majority of the dotfiles located. tdm uses the relative path from `files/` to find where the symlink should be located. `(files/relative_path` creates a symlink `$HOME/relative_path` -> `files/relative_path`)
- `forks`: For holding different versions of a dotfile. When you create a fork the forked version will be held inside here.


To start using your new dotfiles repo run:

```bash
tdm deploy PATH
```
Where `PATH` is the location of your repository.

To add dotfiles to tdm run:

```bash
tdm add PATH
```

Here path can be a file or a directory. If it is a directory, tdm remembers this and if a new file appears here it will automatically add it, (if the directory is not symlinked itself of course) when running `tdm patch`.


You can specify your profiles in the `config.toml`. If you want to switch between them use:
```bash
tdm use PROFILE
```
The *base* profile is a default profile that you can't remove. It is the default profile that you use.
When you are not using the *base* profile, you can create *forks* of the dotfiles you added.
Fork creates a new file inside `forks/PROFILE/relative_path` and the target of the symlink will instead to files point here.


The last command I will introduce you it is `tdm git`. This command I will run the git commands and options specified but inside the currently used repository. So, to quickly commit the changes to your dotfiles you can run: `tdm git add ./`, `tdm git commit -m "Tweaking my dotfiles."` and lastly `tdm git push`.




















