const std = @import("std");
const cli = @import("cli.zig");
const yazap = @import("yazap");
const commands = @import("commands.zig");

const App = yazap.App;
const Arg = yazap.Arg;

pub fn main() anyerror!void {
    var arena = std.heap.ArenaAllocator.init(std.heap.page_allocator);
    defer arena.deinit();

    const allocator = arena.allocator();

    var app: App = App.init(allocator, "tdm", null);
    defer app.deinit();
    _ = try cli.configureCli(&app);

    const matches = try app.parseProcess();

    inline for (commands.commands) |subcommand| {
        if (matches.subcommandMatches(subcommand)) |sub_matches| {
            @field(commands, subcommand)(&sub_matches);
            return;
        }
    }

    //TODO:
    //
    // if (matches.subcommandMatches("git")) |_| {
    //     commands.git(app.process_args); // vymaz tdm, zbytek zavolej z tdm repa
    // }
    //
    //
}
