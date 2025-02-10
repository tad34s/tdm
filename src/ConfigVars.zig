const std = @import("std");
const Self = @This();
const State = @import("State.zig");

allocator: std.mem.Allocator,
vars_map: std.StringHashMap([][]const u8),

pub fn init(allocator: std.mem.Allocator, state: *const State) !Self {
    const self = Self{
        .allocator = allocator,
        .vars_map = std.StringHashMap([][]const u8).init(allocator),
    };
    errdefer self.deinit();
    try self.populate(state);
    return self;
}

// TODO:
/// Populate the vars_map with vars parsed from the config.toml.
fn populate(self: *const Self, state: *const State) !void {
    // mby const u Self dat pryc uvidim
    _ = self;
    _ = state;
    return;
}

// bude potreba stuff jake get val

pub fn deinit(self: *Self) void {
    var it = self.vars_map.iterator();
    while (it.next()) |entry| {
        self.allocator.free(entry.key_ptr);
        self.allocator.free(entry.value_ptr);
    }
    self.vars_map.deinit();
}
