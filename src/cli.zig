const std = @import("std");
const yazap = @import("yazap");

const App = yazap.App;
const Arg = yazap.Arg;
const Command = yazap.Command;

pub fn configureCli(app: *App) !*Command {
    var tdm: *Command = app.rootCommand();
    tdm.setProperty(.help_on_empty_args);

    // Init
    var init_cmd = app.createCommand("init", "Create a directory with a sample dotfiles repo.");
    try init_cmd.addArgs(&[_]Arg{
        Arg.singleValueOption("name", 'n', "Name of the created directory"),
    });

    // Add
    var add_cmd = app.createCommand("add", "Add a file or a directory to the dotfiles repo.");
    try add_cmd.addArgs(&[_]Arg{
        Arg.positional("FILE", null, 0),
    });

    // Save
    // TODO: auto mergovat tempalty?
    var save_cmd = app.createCommand("save", "Save changes made to the managed files");
    try save_cmd.addArgs(&[_]Arg{
        Arg.booleanOption("quiet", 'q', "Disable prompting, automaticaly overwrite the source file, skip templates."),
    });

    // Edit
    var edit_cmd = app.createCommand("edit", "Open the source file an a text editor.");
    try edit_cmd.addArgs(&[_]Arg{
        Arg.positional("FILE", "The file to edit", 0),
    });

    // Template
    var temp_cmd = app.createCommand("temp", "Create a template from the file specified.");
    try temp_cmd.addArgs(&[_]Arg{
        Arg.positional("FILE", null, 0),
    });

    //Apply
    var apply_cmd = app.createCommand("apply", "Apply the dotfiles, if no config is specified apply the last config used.");
    try apply_cmd.addArgs(&[_]Arg{
        Arg.singleValueOption("config", 'c', "If it is left empty will revert to using only global variables."),
    });

    //Use
    var use_cmd = app.createCommand("use", "Pick a tdm dotfiles repo which to use.");
    try use_cmd.addArgs(&[_]Arg{
        Arg.singleValueOption("git-repo", 'g', "Pull tdm dotfiles from a git repository"),
        Arg.singleValueOption("path", 'p', "Relative or absolute path to the new tdm repo"),
        Arg.singleValueOption("name", 'n', "Change the name of the repo"),
        Arg.singleValueOption("config", 'c', "Apply the config specified"),
    });

    //Update
    const update_cmd = app.createCommand("update", "Pull changes to the dotfiles repo, apply them");

    //Status
    const status_cmd = app.createCommand("status", "Display changes between the dotfiles and their source files.");

    const git_cmd = app.createCommand("git", "Call git commands from the dotfiles repo in use");

    try tdm.addSubcommands(&[_]yazap.Command{
        init_cmd,
        add_cmd,
        save_cmd,
        edit_cmd,
        temp_cmd,
        apply_cmd,
        use_cmd,
        update_cmd,
        status_cmd,
        git_cmd,
    });

    return tdm;
}
