const std = @import("std");
const yazap = @import("yazap");
const print_to_user = @import("../print_to_user.zig");
const State = @import("../State.zig");

const printError = print_to_user.printError;
const printSuccess = print_to_user.printSuccess;

pub fn addCmd(allocator: std.mem.Allocator, matches: *const yazap.ArgMatches) void {
    const state = try State.loadState(allocator);
    const src_dir = try state.getSrc();

    _ = src_dir;
    if (matches.getSingleValue("FILE OR DIR")) |path| {
        // figure out if it is a dir of file
        // if dir use copy -r
        // if file just copy the file
        // maintain the path of the file from home
        _ = path;
    } else return;

    printSuccess("New dotfiles created successfully.\n", .{});
}
