const std = @import("std");
const yazap = @import("yazap");
const State = @import("../State.zig");

const print_to_user = @import("../print_to_user.zig");

const printError = print_to_user.printError;
const printSuccess = print_to_user.printSuccess;

pub fn deployCmd(allocator: std.mem.Allocator, matches: *const yazap.ArgMatches) void {

    // Check if argument correct

    if (matches.getSingleValue("REPO_OR_PATH") == null) return;
    const repo_or_path = matches.getSingleValue("REPO_OR_PATH").?;

    const dotfiles_dir = std.fs.cwd().openDir(
        repo_or_path,
        .{},
    ) catch |err| {
        printError("Invalid directory provided: {s}", err);
    };

    // Create state
    var new_state = State.init(
        allocator,
        dotfiles_dir,
        matches.getSingleValue("profile"),
    );

    // Check validity
    if (!new_state.checkValidDotfiles()) {
        printError("Could not read dofiles repo: {s}", error.NotTDMRepo);
    }

    // Save to applications data directory

    new_state.serialize() catch |err| {
        printError("Failed to serialize state: {s}", err);
    };

    // Apply state
    new_state.loadVars() catch |err| {
        printError("Failed parsing config.toml: {s}", err);
    };
    new_state.applyConfig() catch |err| {
        printError("Failed to apply the specified dotfiles: {s}", err);
    };

    // Run bootstrap
    if (matches.containsArg("bootstrap")) {
        new_state.runBootstrap() catch |err| {
            printError("Failed running bootstrap: {s}", err);
        };
    }

    printSuccess("Successfully switched dotfiles!\n", .{});
}
