// Currently implemented commands
pub const commands = [_][:0]const u8{
    "init",
    "deploy",
};

pub const init = @import("commands/init.zig").initCmd;
pub const deploy = @import("commands/deploy.zig").deployCmd;
