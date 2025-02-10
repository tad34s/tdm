const std = @import("std");

pub fn getDataDir(allocator: std.mem.Allocator) !std.fs.Dir {
    const data_dir: []const u8 = try std.fs.getAppDataDir(allocator, "tdm");
    defer allocator.free(data_dir);

    return std.fs.cwd().makeOpenPath(
        data_dir,
        .{},
    );
}
