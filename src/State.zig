const std = @import("std");
const ConfigVars = @import("ConfigVars.zig");

const Self = @This();

allocator: std.mem.Allocator,
dotfiles_dir: std.fs.Dir,
profile_name: ?[]const u8,
config_vars: ?ConfigVars = null,

pub fn init(
    allocator: std.mem.Allocator,
    dotfiles_dir: std.fs.Dir,
    profile_name: ?[]const u8,
) Self {
    return Self{
        .allocator = allocator,
        .dotfiles_dir = dotfiles_dir,
        .profile_name = profile_name,
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

pub fn loadVars(self: *Self) !void {
    std.debug.print("Loading vars...\n", .{});
    self.config_vars = try ConfigVars.init(self.allocator, self);
}

/// Regenerate and apply the dotfiles
/// Vars have to be loaded
pub fn applyConfig(self: *const Self) !void {
    std.debug.print("Applying config...\n", .{});
    std.debug.assert(self.config_vars != null);
    // try clearGenDir();
    // const virt_files = try generateFiles(&config_vars);
    // try virt_files.writeToFs();
    // try stowGenFiles();
}

/// Call the bootstrap script.
/// Vars need to be loaded.
pub fn runBootstrap(self: *Self) !void {
    std.debug.print("Running bootstrap...\n", .{});
    std.debug.assert(self.config_vars != null);
}

// TODO:
/// Clear the tdm/gen directory
fn clearGenDir() !void {
    return;
}
