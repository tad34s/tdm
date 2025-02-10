const std = @import("std");
const Self = @This();

allocator: std.mem.Allocator,
vars_map: std.StringHashMap([][]const u8),

// TODO:
pub fn runBootstrap(self: *Self) void {
    std.debug.print("Running bootstrap...\n", .{});
    _ = self;
}
pub fn applyConfig(self: *Self) void {
    std.debug.print("Applying config...\n", .{});
    _ = self;
}

pub fn deinit(self: *Self) void {
    var it = self.vars_map.iterator();
    while (it.next()) |entry| {
        self.allocator.free(entry.key_ptr);
        self.allocator.free(entry.value_ptr);
    }
    self.vars_map.deinit();
}
