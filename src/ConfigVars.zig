const std = @import("std");
const Self = @This();
const State = @import("State.zig");
const toml = @import("zig-toml");

allocator: std.mem.Allocator,
ignore_files: [][]const u8,
exclude_files: [][]const u8,
use_only: ?[][]const u8,
vars_map: std.StringHashMap([]const u8),

//TODO: Consider adding more error messages.

const ConfigVarsInterMed = struct {
    ignore_files: std.ArrayList(toml.Value),
    exclude_files: std.ArrayList(toml.Value),
    include_files: std.ArrayList(toml.Value),
    use_only: std.ArrayList(toml.Value),
    vars: std.StringHashMap([]const u8),

    pub fn combineConfigVars(global: *ConfigVarsInterMed, profile: *const ConfigVarsInterMed) !void {
        var it = profile.vars.iterator();
        while (it.next()) |entry| {
            if (!global.vars.contains(entry.key_ptr.*)) {
                std.debug.print("{s}\n", .{entry.key_ptr.*});
                return error.DefaultNotSpecified;
            }
            try global.vars.put(entry.key_ptr.*, entry.value_ptr.*);
        }

        var i: usize = 0;
        const og_len = global.exclude_files.items.len;

        // Remove files that are in the profile include
        // Add excludes that are in the profile exclude
        for (global.exclude_files.items) |item2| {
            // preventing duplicates
            for (profile.exclude_files.items) |item| {
                if (std.mem.eql(u8, item.string, item2.string)) {
                    break;
                } else {
                    try global.exclude_files.append(item);
                }
            }

            for (profile.include_files.items) |item| {
                if (std.mem.eql(u8, item.string, item2.string)) {
                    _ = global.exclude_files.orderedRemove(i);
                    break;
                }
            } else {
                i += 1;
            }

            if (i >= og_len) break;
        }
        global.use_only = profile.use_only;
    }
};

pub fn init(allocator: std.mem.Allocator, state: *const State) !Self {
    var self: Self = undefined;
    self.allocator = allocator;
    self.vars_map = std.StringHashMap([]const u8).init(allocator);
    errdefer self.deinit();
    try self.populate(state);
    return self;
}

/// Populate the vars_map with vars parsed from the config.toml.
fn populate(self: *Self, state: *const State) !void {
    var parser = toml.Parser(toml.Table).init(self.allocator);
    defer parser.deinit();

    const file = try state.dotfiles_dir.openFile("config.toml", .{ .mode = .read_only });
    defer file.close();

    const content = try file.readToEndAlloc(self.allocator, 1024 * 1024 * 1024);
    defer self.allocator.free(content);

    const result = try parser.parseString(content);
    const config = result.value;
    defer result.deinit();
    // deallocates the result -> loadFromIntermed allocates new copies beforehand

    var profile: *toml.Table = undefined;
    for (config.get("profile").?.array.items) |item| {
        if (std.mem.eql(u8, item.table.get("name").?.string, state.profile_name orelse "")) {
            profile = item.table;
        }
    }
    var global_config_vars = organizeTable(self.allocator, &config);
    const profile_config_vars = organizeTable(self.allocator, profile);
    try global_config_vars.combineConfigVars(&profile_config_vars);
    try self.loadFromIntermed(&global_config_vars);
}

pub fn get(self: *Self, key: []const u8) ![]const u8 {
    if (self.vars_map.get(key)) |val| {
        return val;
    } else {
        return error.ValueNotFound;
    }
}

pub fn deinit(self: *Self) void {
    var it = self.vars_map.iterator();
    while (it.next()) |entry| {
        self.allocator.free(entry.key_ptr.*);
        self.allocator.free(entry.value_ptr.*);
    }
    self.vars_map.deinit();
}

// TODO: Could maybe allocate less? :D
///Organize table into intermediate config vars structs.
fn organizeTable(allocator: std.mem.Allocator, vars_parsed: *const toml.Table) ConfigVarsInterMed {
    var output = ConfigVarsInterMed{
        .vars = std.StringHashMap([]const u8).init(allocator),
        .ignore_files = std.ArrayList(toml.Value).init(allocator),
        .exclude_files = std.ArrayList(toml.Value).init(allocator),
        .include_files = std.ArrayList(toml.Value).init(allocator),
        .use_only = std.ArrayList(toml.Value).init(allocator),
    };

    output.vars.put("name", "") catch unreachable; // TODO: Fix

    var it = vars_parsed.iterator();
    while (it.next()) |entry| {
        switch (entry.value_ptr.*) {
            .string => |val| {
                output.vars.put(entry.key_ptr.*, val) catch unreachable; // TODO: Fix
            },
            .array => |val| {
                const special_names = [_][]const u8{
                    "ignore_files",
                    "exclude_files",
                    "include_files",
                    "use_only",
                };
                inline for (special_names) |name| {
                    if (std.mem.eql(u8, name, entry.key_ptr.*)) {
                        @field(output, name).deinit();
                        @field(output, name) = val.*;
                    }
                }
            },
            else => continue,
        }
    }
    return output;
}

/// Finish creating config by reallocating only necessary stuff.
fn loadFromIntermed(self: *Self, intermed: *ConfigVarsInterMed) !void {
    // copy vars
    var it = intermed.vars.iterator();
    while (it.next()) |entry| {
        const new_str_key: []u8 = try self.allocator.alloc(u8, entry.key_ptr.len);
        const new_str_val: []u8 = try self.allocator.alloc(u8, entry.value_ptr.len);
        @memcpy(new_str_key, entry.key_ptr.*);
        @memcpy(new_str_val, entry.value_ptr.*);
        try self.vars_map.put(new_str_key, new_str_val);
    }

    const array_fields = [_][]const u8{
        "ignore_files",
        "exclude_files",
        "use_only",
    };

    // copy arrays
    inline for (array_fields) |name| {
        var ptr = try self.allocator.alloc([]u8, @field(intermed, name).items.len);
        for (@field(intermed, name).items, 0..) |item, i| {
            ptr[i] = try self.allocator.alloc(u8, item.string.len);
            @memcpy(ptr[i], item.string);
        }
        if (std.mem.eql(u8, "use_only", name) and intermed.use_only.items.len == 0) {
            self.use_only = null;
        } else {
            @field(self, name) = ptr;
        }
    }
}
