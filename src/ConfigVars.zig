const std = @import("std");
const Self = @This();

// TODO:
pub fn runBootstrap(self: *Self) void {
    std.debug.print("Running bootstrap", .{});
    _ = self;
}
pub fn applyConfig(self: *Self) void {
    std.debug.print("Applying config", .{});
    _ = self;
}
