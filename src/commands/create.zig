const std = @import("std");
const yazap = @import("yazap");
const print_to_user = @import("../print_to_user.zig");

const printError = print_to_user.printError;
const printSuccess = print_to_user.printSuccess;

pub fn createCmd(allocator: std.mem.Allocator, matches: *const yazap.ArgMatches) void {
    var dir_name: []const u8 = "dotfiles";

    if (matches.getSingleValue("name")) |name| {
        dir_name = name;
    }

    if (matches.getSingleValue("repo")) |repo_link| {
        pullRepo(allocator, repo_link, dir_name) catch |err| {
            printError("Failed pulling repo: {s}", err);
        };
    } else {
        createSampleRepo(dir_name) catch |err| {
            printError("Error accessing filesystem: {s}", err);
        };
    }

    printSuccess("New dotfiles created successfully.\n", .{});
}

fn pullRepo(allocator: std.mem.Allocator, link: []const u8, dir_name: ?[]const u8) !void {

    // Define the git command
    var child: std.process.Child = undefined;
    if (dir_name) |dir| {
        child = std.process.Child.init(&[_][]const u8{ "git", "clone", link, dir }, allocator);
    } else {
        child = std.process.Child.init(&[_][]const u8{ "git", "clone", link }, allocator);
    }

    child.stdin_behavior = .Ignore;
    child.stdout_behavior = .Inherit;
    child.stderr_behavior = .Inherit;

    // Run the command
    try child.spawn();
    const term = try child.wait();

    if (term.Exited != 0) {
        return error.GitPullFailed;
    }
}

fn createSampleRepo(dir_name: []const u8) !void {
    // Create directories
    const dotfiles_dir = try std.fs.cwd().makeOpenPath(dir_name, .{});
    const subdirs = [_][]const u8{ "src", "bin" };

    for (subdirs) |subdir| {
        try dotfiles_dir.makePath(subdir);
    }

    const sample_config_file = try dotfiles_dir.createFile("config.toml", .{ .read = true });
    defer sample_config_file.close();
    try sample_config_file.writeAll(sample_file);
}

const sample_file =
    \\
    \\font = "JetBrainsNerd Monospace"  # global vars
    \\bootstrap = ""          # global var
    \\git-email = "default@email.cz"
    \\
    \\exclude-files = [                 # global exclude
    \\  ".picom.tdmt"
    \\]
    \\
    \\ignore-files = [ # ignore when recursively adding
    \\ ".lazy-lock.json"
    \\]
    \\
    \\[[profile]]                       # profile
    \\name = "linux-dev"
    \\git-email = "bacatade@fit.cvut.cz"  # var
    \\bootstrap = "linux.sh"             # overriding
    \\
    \\[[profile]]                       # profile
    \\name = "mac"
    \\git-email = "tadeas.baca@blindspot.com"  # var
    \\include-files = [                        # special, includuje
    \\  ".picom.tdmt"
    \\]
    \\
    \\[[profile]]                       # profile
    \\name = "server"
    \\git-email = "bacatade@fit.cvut.cz"
    \\use-only = [                            # pouzivej jenom tyhle
    \\  "nvim"
    \\]
;

test createSampleRepo {
    const tmp_dir = try std.testing.tmpDir();
    defer tmp_dir.close();

    const test_dir = try tmp_dir.makeOpenPath("test_dotfiles", .{});
    try createSampleRepo("test_dotfiles");

    var file = try test_dir.openFile("config.toml", .{ .read = true });
    defer file.close();

    var buffer: [256]u8 = undefined;
    const bytes_read = try file.read(&buffer);
    std.testing.expect(bytes_read > 0);
}
