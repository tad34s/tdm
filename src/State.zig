const std = @import("std");
const ConfigVars = @import("ConfigVars.zig");

const Self = @This();

allocator: std.mem.Allocator,
dotfiles_dir: std.fs.Dir,
profile_name: ?[]const u8,
bootstrap: bool = false,
config_vars: ?ConfigVars = null,

pub fn init(allocator: std.mem.Allocator, dotfiles_location: []const u8, profile_name: ?[]const u8, bootstrap: bool) Self {
    return Self{
        .allocator = allocator,
        .dotfiles_location = dotfiles_location,
        .profile_name = profile_name,
        .bootstrap = bootstrap,
    };
}

pub fn deinit(self: *Self) void {
    if (self.config_vars) |cnfg_vars| {
        cnfg_vars.deinit();
    }
}

/// Save the state members in a file called "state" in the `data_dir` directory.
pub fn serialize(self: *const Self, data_dir: *const std.fs.Dir) !void {
    // open state file
    const state_file: std.fs.File = data_dir.openFile("state", .{ .mode = .write_only }) catch |err| blk: {
        if (err == error.FileNotFound) {
            const new_state_file = try data_dir.createFile("state", .{ .read = true });
            break :blk new_state_file;
        }
        return err;
    };
    defer state_file.close();

    const file_writer = state_file.writer();

    var path_buffer: [std.fs.MAX_PATH_BYTES]u8 = undefined;
    const path = try std.os.getFdPath(self.dotfiles_dir.fd, &path_buffer);

    try file_writer.print("{s}\n{s}\n", .{ path, self.profile_name orelse "" });
}

///Check if the directory provided seems like a tdm repository.
pub fn checkValidDotfiles(self: *const Self) bool {
    self.dotfiles_dir.access("config.toml", .{}) catch {
        return false;
    };
    self.dotfiles_dir.access("src", .{}) catch {
        return false;
    };

    return true;
}

// TODO:
/// Load profile from the repo.
/// Popluates the config_vars field.
fn loadProfile(self: *Self) !void {
    std.debug.assert(self.config_vars == null);
    self.config_vars = ConfigVars.init();
    _ = self;
    return .{};
}

pub fn applyConfig(self: *const Self) !void {
    std.debug.print("Applying config...\n", .{});
    _ = self;
}
