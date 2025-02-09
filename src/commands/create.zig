const std = @import("std");
const yazap = @import("yazap");

pub fn createCmd(allocator: std.mem.Allocator, matches: *const yazap.ArgMatches) !void {
    var dir_name: []const u8 = "dotfiles";

    if (matches.getSingleValue("name")) |name| {
        dir_name = name;
    }

    if (matches.getSingleValue("repo")) |repo_link| {
        try pullRepo(allocator, repo_link, dir_name);
    } else {
        try createSampleRepo(dir_name);
    }
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
        std.debug.print("git pull failed with exit code: {}\n", .{term.Exited});
    } else {
        std.debug.print("git pull successful!\n", .{});
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
