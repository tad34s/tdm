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

- [ ] save
  - currently using -> src 
  - pokud je spec. v directories a neni v src - prida se (a file existuje)
- [ ] load
  - src -> currently using
- [ ] update
  - pull + load 

- add nemusim delat actually

## Ideas
- add `.gitignore` to a thermos repo, will contain `/.thermos-cache`
- in this repo the hash of the config and src will be stored, -> quickly detecting changes.

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
   templates = ["config.ini"]
}
```

```yaml
directories:
  ~/project:
    exclude:
      - node_modules
      - .git
  ~/bin: {}
  config:
    nvim:
      exclude:
        - lazy-lock.json
    picom.conf:
      template: true
    polybar:
      templates:
        - config.ini
```
