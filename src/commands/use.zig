const std = @import("std");
const yazap = @import("yazap");
const State = @import("../State.zig");
const print_to_user = @import("../print_to_user.zig");

const printError = print_to_user.printError;
const printSuccess = print_to_user.printSuccess;

pub fn useCmd(allocator: std.mem.Allocator, matches: *const yazap.ArgMatches) void {

    // Check if argument correct
    if (matches.getSingleValue("DIR") == null) return;

    const dotfiles_dir = std.fs.cwd().openDir(
        matches.getSingleValue("DIR").?,
        .{},
    ) catch |err| {
        printError("Invalid directory provided: {s}", err);
    };

    // Create state
    const new_state = State{
        .dotfiles_dir = dotfiles_dir,
        .profile_name = matches.getSingleValue("profile"),
        .bootstrap = matches.containsArg("bootstrap"),
    };

    // Check validity
    if (!new_state.checkValidDotfiles()) {
        printError("Could not read dofiles repo: {s}", error.NotTDMRepo);
        return;
    }

    // Save to applications data directory
    const data_dir = getDataDir(allocator) catch |err| {
        printError("Could not access applications data directory: {s}", err);
    };

    new_state.serialize(&data_dir) catch |err| {
        printError("Failed to serialize state: {s}", err);
    };

    // Apply state
    new_state.applyConfig() catch |err| {
        printError("Failed to apply the specified dotfiles: {s}", err);
    };

    printSuccess("Successfully switched dotfiles!\n", .{});
}

fn getDataDir(allocator: std.mem.Allocator) !std.fs.Dir {
    const data_dir: []const u8 = try std.fs.getAppDataDir(allocator, "tdm");
    defer allocator.free(data_dir);

    return std.fs.cwd().makeOpenPath(
        data_dir,
        .{},
    );
}
