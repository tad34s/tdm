// Currently implemented commands
pub const commands = [_][:0]const u8{
    "init",
};

pub const init = @import("commands/init.zig").initCmd;
