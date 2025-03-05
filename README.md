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


## TODOS
- thermos or tdm?
- prepare sample config
- [ ] create
   - [x] repo jako optinal arg?
   - [ ] check for overwrites, change name?
   

## Ideas
- add `.gitignore` to a thermos repo, will contain `/.thermos-cache`
- in this repo the hash of the config and src will be stored, -> quickly detecting changes.

- jak udelat linking?
 1. add -> do src -> generator -> datafiles/using -> stow -> links
    - vyhody je relativne lehke implementace, zadne veci navic, spis se nebreakne
    - nevyhohody - unfolding?
- jak fixnout to ze chci ignorovat files?
- tdm diff zavolat na directory, 2. 3. vrstvu

--------

--> tdm by keepovalo nests/targets
zde deklaritivne clovek zadefinuje co hlidat
+ command add to automaticky prida
- jde pridavat vyjimky
+ command exclude automaticky prida vyjimku

pak by slo vypsat jake configy jsou zmenene

moznosti:
```tdm
+ ~/project
  - node_modules
  - .git
+ ~/bin
+ config
  + nvim
    - lazy-lock.json
  @ picom.conf
  + polybar
    @ config/config.ini
```

```toml
[directories]
"~/project" = { exclude = ["node_modules", ".git"] }
"~/bin" = {}
"config" = {}

[directories.config]
"nvim" = { exclude = ["lazy-lock.json"]}
"picom.conf" = { template = true }
"polybar" = { 
   "config/config.ini" = {template = true}
}
```



