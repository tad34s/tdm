const std = @import("std");
const ConfigVars = @import("ConfigVars.zig");

const Self = @This();

file_location: []const u8,

profile_name: ?[]const u8,

/// Save the state members in a file called "state" in the `data_dir` directory.
pub fn serialize(self: *Self, data_dir: *std.fs.Dir) void {
    const state_file: std.fs.File = data_dir.openFile("state", .{ .read = true }) catch |err| blk: {
        if (err == error.OpenError) {
            const new_state_file = try data_dir.createFile("state", .{ .read = true });
            break :blk new_state_file;
        }
        return err;
    };
    defer state_file.close();

    const file_writer = state_file.writer();
    file_writer.print("{s}\n{s}\n", .{ self.file_location, self.profile_name }) catch |err| {
        std.debug.print("Fatal Error: Unable to write to file: {}\n", .{err});
        std.process.exit(1);
    };
}

// TODO:
/// Load profile from the repo.
pub fn loadProfile(self: *Self) ConfigVars {
    _ = self;
    return .{};
}
