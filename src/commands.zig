// Currently implemented commands
pub const commands = [_][:0]const u8{
    "create",
    "use",
};

pub const create = @import("commands/create.zig").createCmd;
pub const use = @import("commands/use.zig").useCmd;
