const std = @import("std");
const yazap = @import("yazap");

pub fn initCmd(matches: *const yazap.ArgMatches) void {
    if (matches.getSingleValue("name")) |name| {
        std.log.info("config pattern = {s}", .{name});
        return;
    }
}
