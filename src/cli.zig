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
        Arg.positional("NAME", "Name of the created directory", null),
        // Arg.positional("REPO", "Link to a git repository", null),
    });

    // Deploy
    var deploy_cmd = app.createCommand("deploy", "Activate the tdm repo selected and symlink the dotfiles.");
    try deploy_cmd.addArgs(&[_]Arg{
        Arg.positional("REPO_OR_PATH", "Link to a git repository", null),
        Arg.singleValueOption("profile", 'p', "Profile to right away switch to."),
        Arg.booleanOption("bootstrap", 'b', "Run the bootstrap again"),
    });
    deploy_cmd.setProperty(.help_on_empty_args);

    // Vacate
    var vacate_cmd = app.createCommand("vacate", "Stop using the tdm repo. Will replace all symlinks with original files.");
    try vacate_cmd.addArgs(&[_]Arg{
        Arg.booleanOption("keep", 'k', "Replace the symlinks with copies."),
    });

    // Edit
    // var edit_cmd = app.createCommand("edit", "Open the source file an a text editor.");
    // try edit_cmd.addArgs(&[_]Arg{
    //     Arg.positional("FILE", "The file to edit", 0),
    // });

    // Template
    // var temp_cmd = app.createCommand("fork", "Create a template from the file specified.");
    // try temp_cmd.addArgs(&[_]Arg{
    //     Arg.positional("FILE", null, 0),
    // });

    //Apply
    // var apply_cmd = app.createCommand("apply", "Apply the dotfiles, if no profile is specified apply the last profile used.");
    // try apply_cmd.addArgs(&[_]Arg{
    //     Arg.singleValueOption("profile", 'p', "If it is left empty will revert to using only global variables."),
    // });

    // Use
    var use_cmd = app.createCommand("use", "Pick which profile to use.");
    try use_cmd.addArgs(&[_]Arg{
        Arg.positional("PROFILE", "", null),
        Arg.booleanOption("bootstrap", 'b', "Run the bootstrap again"),
    });

    const patch_cmd = app.createCommand("patch", "Add new files to tdm repo. Remove not needed files.");
    //Update
    // const update_cmd = app.createCommand("update", "Pull changes to the dotfiles repo, apply them");

    //Status
    // const status_cmd = app.createCommand("status", "Display changes between the dotfiles and their source files.");

    // const git_cmd = app.createCommand("git", "Call git commands from the dotfiles repo in use");

    try tdm.addSubcommands(&[_]yazap.Command{
        init_cmd,
        deploy_cmd,
        vacate_cmd,
        use_cmd,
        patch_cmd,
    });

    return tdm;
}
