const std = @import("std");
const builtin = @import("builtin");
const stderr = std.io.getStdErr().writer();
const stdout = std.io.getStdOut().writer();

/// In Debug mode panic with message.
/// In release modes print message to stderr and exit the proccess.
/// Use {s} in message to for printing error name.
pub inline fn printError(comptime msg: ?[]const u8, err: anyerror) void {
    if (msg) |msg_| {
        if (builtin.mode == .Debug) {
            std.debug.panic(msg_, .{@errorName(err)});
        } else {
            stderr.print(" " ++ msg_, .{@errorName(err)}) catch {};
            std.process.exit(@intCast(@intFromError(err)));
        }
    } else {
        if (builtin.mode == .Debug) {
            std.debug.panic("{s}", .{@errorName(err)});
        } else {
            std.process.exit(@intCast(@intFromError(err)));
        }
    }
    return;
}

/// For printing that the command has succeeded.
pub inline fn printSuccess(comptime format: []const u8, args: anytype) void {
    stdout.print(" " ++ format, args) catch |err| {
        printError("Could not print to StdOut: {s}", err);
    };
}
