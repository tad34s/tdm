const std = @import("std");
const yazap = @import("yazap");

const App = yazap.App;
const Arg = yazap.Arg;
const Command = yazap.Command;

pub fn configureCli(app: *App) !*Command {
    var tdm: *Command = app.rootCommand();
    tdm.setProperty(.help_on_empty_args);

    // Create
    var create_cmd = app.createCommand("create", "Create a directory with a sample dotfiles repo.");
    try create_cmd.addArgs(&[_]Arg{
        Arg.singleValueOption("name", 'n', "Name of the created directory"),
        Arg.positional("repo", "Link to a git repository", null),
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
    var apply_cmd = app.createCommand("apply", "Apply the dotfiles, if no profile is specified apply the last profile used.");
    try apply_cmd.addArgs(&[_]Arg{
        Arg.singleValueOption("profile", 'p', "If it is left empty will revert to using only global variables."),
    });

    // Use
    // TODO: call bootstrap on first use
    // - detect first use with hashed?
    // - loading the toml atd.
    var use_cmd = app.createCommand("use", "Pick which tdm dotfiles repo to use.");
    try use_cmd.addArgs(&[_]Arg{
        Arg.positional("Dir", "Relative or absolute path to the new tdm repo", null),
        Arg.singleValueOption("profile", 'p', "Apply the profile specified"),
        Arg.booleanOption("bootstrap", 'b', "Run the bootstrap again"),
    });

    //Update
    const update_cmd = app.createCommand("update", "Pull changes to the dotfiles repo, apply them");

    //Status
    const status_cmd = app.createCommand("status", "Display changes between the dotfiles and their source files.");

    const git_cmd = app.createCommand("git", "Call git commands from the dotfiles repo in use");

    try tdm.addSubcommands(&[_]yazap.Command{
        create_cmd,
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
