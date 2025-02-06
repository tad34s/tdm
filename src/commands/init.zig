const std = @import("std");
const yazap = @import("yazap");

pub fn initCmd(matches: *const yazap.ArgMatches) !void {
    var dir_name: []const u8 = "dotfiles";

    if (matches.getSingleValue("name")) |name| {
        dir_name = name;
    }

    // Create directories
    const dotfiles_dir = try std.fs.cwd().makeOpenPath(dir_name);
    const subdirs = [_][]const u8{ "src", "bin" };

    for (subdirs) |subdir| {
        try dotfiles_dir.makePath(subdir);
    }

    const sample_config_file = try dotfiles_dir.createFile("config.toml", .{ .read = true });
    try sample_config_file.writeAll();
    defer sample_config_file.close();
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
