const std = @import("std");
const yazap = @import("yazap");
const State = @import("../State.zig");

pub fn useCmd(allocator: std.mem.Allocator, matches: *const yazap.ArgMatches) void {
    const app_data_dir: std.fs.Dir = try std.fs.cwd().makeOpenPath(
        try std.fs.getAppDataDir(allocator, "tdm"),
        .{},
    );

    const buffer_ptr = allocator.alloc(u8, std.fs.MAX_PATH_BYTES);
    defer allocator.free(buffer_ptr);

    const new_state = State{
        .profile_name = matches.getSingleValue("profile"),
        .file_location = app_data_dir.realpath(".", buffer_ptr),
    };

    new_state.serialize(&app_data_dir);

    const config_vars = new_state.loadProfile();

    // call bootstrap
    if (matches.getSingleValue("bootstrap")) |_| {
        config_vars.runBootstrap();
    }

    config_vars.applyConfig();
}
